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

from .drone import letter_marks, start_breves, without_breves
from .fermatas import fermatas, on_fermata
from .layers import read_layers
from .meter import COMMON_ROWS, mid_signs, page_meter
from . import meter as _meter_mod
from .music import MIDDLE, agree_lengths, bar_sums, build_staff, full_sum, held, key_alters, musicxml, pitch_of, staff_columns
from . import music as _music
from . import classify
from . import grammar as _grammar
from . import headnet
from . import rests as _rests_mod
from .rests import block_rests, eighth_rests, in_rest, quarter_rests, rest_dot
from .signs import bar_signs, note_signs
from .starts import read_start, read_starts
from .symbols import line_gap_stems, arc_pairs, bar_stems, arc_wholes, open_wholes, bar_lines, bar_marks, faint_bars, big_holes, broken_stems, count_tails, dots, hole_heads, loops_have_flags, lost_stems, gone_stems, chord_stems, read_symbols, \
    ring_heads, slit_page, thin_heads, without_bar_pieces, without_end_marks, without_flag_curls, without_flag_loops, without_flag_strokes, without_flag_trails, without_flat_cells, without_clip_cells, without_grey_marks, without_f_marks, without_line_marks, without_p_bowls, without_row_letters, without_beam_pieces, without_bow_middles, without_stem_end_marks, without_top_loops, without_far_marks, without_stem_meets, without_dot_columns, without_stem_spans, without_joints, without_upright_holes, chord_wholes, dotless_wholes, grace_notes
from .ties import read_ties
from .triplets import mark_triplets
from .words import cut_stems, word_bands, word_rows

SIGNS = 'strokes'
TIMES = True         # the numbers of a time signature in the middle of a staff are no notes (scorereader.meter)
# The staves of a system show their time signature in the same columns. A head of a staff that shows no time signature
# there, in the columns of the numbers that the nearest staff of its system shows, or of its bold C
# (`meter.COMMON_BOLD`), is a number of its own staff's time signature (or its C) that the reading of the signs missed: a
# hand's 4 that a pen stroke joins, numbers that touch the key, the clef or each other, a C of a heavy print. A census of
# every read note of LitChoir's pages in the columns of another staff's time signature (56 marks on 33 pages, each looked
# at) found numbers and Cs, and true notes in three places: beside a thin C that `meter.common_signs` read from a head
# or a stem (two pages), and a chord of the lowest staff of a slanted page, where the Cs of the staves drift by half a
# staff space from staff to staff and the chord stands in the columns of the Cs three to five staves over it. A thin C
# is not asked, and only the nearest staves that show a time signature are. At the reader's step the rule takes 55
# marks on 31 pages, each looked at: numbers and pieces of Cs. No head of the fresh set stands in such columns.
TIME_COLUMN = True
TIME_SEEN = None     # a list: the heads that TIME_COLUMN takes, for a census
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
HEADNET_FLIP = 0.8   # with the weights of the small network (scorereader.headnet; SCOREREADER_HEADNET), a head is read as the
                     # other kind (hollow for filled, filled for hollow) where the network is at least this sure of that
                     # kind. Each page of LitChoir read with the network that never saw its hymn: 152 lengths mended and
                     # 19 broken at 0.8 (42 and 2 at 0.9); on the fresh set 9 heads turn and no note is lost. None, or
                     # SCOREREADER_HEADNET=off: off


def page_starts(grey: np.ndarray, places: list[dict], layers: dict | None = None) -> list[dict]:
    """Read the clef and key signature at the start of each staff for the hymn key vote."""
    if not places:
        return []
    if layers is None:
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
    every = [note for bar in built for note in bar if not note.get('rest')]
    for block in sorted(blocks, key=lambda block: block['x']):
        quarter = block.get('kind') != 'block'
        if not quarter and REST_APART is not None and _between_stems(block, every, space):
            continue
        measure = sum(1 for x in edges if x < block['x'])
        if measure not in measures:
            continue
        number = measures.index(measure)
        notes = [note for note in built[number] if not note.get('rest')]
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
            # A quarter or short rest belongs to the voice named by its vertical shift, when that voice leaves room.
            voice = 1 if block['middle'] <= -REST_QUARTER else 2 if block['middle'] >= REST_QUARTER else None
            if voice is None and len(gaps) == 1:
                voice = next(iter(gaps))
            if voice in gaps:
                rest_len = Fraction(block.get('length', 1))
                key = (number, voice) + gaps[voice]
                quarters[key] = quarters.get(key, Fraction(0)) + rest_len
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
    # The non-block rests of a gap occupy the tail of the gap when the gap holds their total length.
    for (number, voice, begin, until), total_len in sorted(quarters.items()):
        if until - begin >= total_len and not any(rest['voice'] == voice and rest['onset'] < until and until - total_len < rest['onset'] + rest['length']
                                                  for rest in out.get(number, [])):
            out.setdefault(number, []).append({'voice': voice, 'onset': until - total_len, 'length': Fraction(total_len)})
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


def other_time(head: dict, staves: list[dict], starts: list[dict], times: dict, space: float) -> bool:
    """Whether the head lies in the columns of a time signature that the nearest staff of its system shows (numbers, or a
    bold C), where its own staff shows none (TIME_COLUMN)."""
    def signs(index):
        return ([starts[index]['time']] if starts[index].get('time') else []) + times.get(index, [])
    own = head['staff']
    near = [(abs(index - own), index) for index, staff in enumerate(staves)
            if index != own and staff['system'] == staves[own]['system'] and signs(index)]
    if not near:
        return False
    closest = min(gap for gap, _ in near)
    for _, index in near:
        if abs(index - own) != closest:
            continue
        for sign in signs(index):
            if sign.get('common') and not sign.get('bold'):
                continue
            if sign.get('oversized') and staves[index]['system'] > 0:
                continue
            if not sign['x0'] - 0.2 * space <= head['cx'] <= sign['x1'] + 0.2 * space:
                continue
            if any(mine['x0'] - space <= sign['x1'] and mine['x1'] + space >= sign['x0'] for mine in signs(own)):
                continue
            if TIME_SEEN is not None:
                TIME_SEEN.append({'x': float(head['cx']), 'y': float(head['cy']), 'staff': own, 'other': index,
                                  'x0': sign['x0'], 'x1': sign['x1'], 'common': bool(sign.get('common'))})
            return True
    return False


def _rest_length(rest: dict, empty_bar: bool, bar_beats: Fraction | None) -> Fraction:
    """Computes the musical duration of a rest, using bar_beats only for hanging whole-bar rests in empty bars."""
    kind = rest.get('kind', 'quarter')
    length = Fraction(rest.get('length', 1))
    if kind == 'block' and rest.get('hangs') and not rest.get('sits'):
        return bar_beats if (bar_beats is not None and empty_bar) else Fraction(4)
    return length


def _voice_free_before(cols: list[list[dict]], target_x: float) -> dict[int, Fraction]:
    """Simulates build_staff() onset progression over columns strictly before target_x."""
    free = {1: Fraction(0), 2: Fraction(0)}
    last_onset, last_shortest = None, None
    for column in sorted(cols, key=lambda c: c[0]['x']):
        if column[0]['x'] >= target_x:
            break
        voices = {ev['voice'] for ev in column}
        onset = max(free[v] for v in voices)
        if last_onset is not None and onset <= last_onset:
            onset = last_onset + last_shortest
        for v in voices:
            free[v] = onset + min(ev['length'] for ev in column if ev['voice'] == v)
        last_onset = onset
        last_shortest = min(ev['length'] for ev in column)
    return free


def _insert_shared_rests(staff: dict, plan: list[list[list[dict]]], bars: list[float],
                         rest_list: list[dict], space: float,
                         bar_beats: Fraction | None = None) -> tuple[list[list[list[dict]]], list[dict]]:
    """Inserts shared-column and non-spanned rests into bar plans before build_staff() so onsets advance cleanly.

    Returns (updated_plan, leftover_single_voice_rests) where leftover rests overlap another voice's notes,
    represent a silent voice's hanging whole-bar rest in a bar with notes, or are spanned by another voice
    (handled by voice_rests()).
    """
    if not rest_list:
        return plan, []
    edges = [x for x in sorted(bars) if staff['x0'] + 2 * space < x < staff['x1'] - space]
    bar_map: dict[int, list[list[dict]]] = {}
    for bar in plan:
        if bar and bar[0]:
            m_idx = sum(1 for x in edges if x < bar[0][0]['x'])
            bar_map[m_idx] = [list(col) for col in bar]

    by_bar: dict[int, list[dict]] = {}
    for rest in sorted(rest_list, key=lambda r: r['x']):
        m_idx = sum(1 for x in edges if x < rest['x'])
        by_bar.setdefault(m_idx, []).append(rest)

    leftover: list[dict] = []
    for m_idx in sorted(by_bar):
        m_rests = by_bar[m_idx]
        cols = bar_map.get(m_idx)
        bar_events = [ev for col in (cols or []) for ev in col if not ev.get('rest')]
        active_voices = sorted({ev['voice'] for ev in bar_events}) or [1]

        free_rests: list[dict] = []
        first_note_x = min((ev['x'] for ev in bar_events), default=float('inf'))
        for rest in m_rests:
            overlaps_note = any(rest['x0'] - 0.55 * space <= ev['x'] <= rest['x1'] + 0.55 * space for ev in bar_events)
            kind = rest.get('kind', 'quarter')
            # Route hanging whole-bar rests of a silent voice (1-voice solo bar, or standing alongside/after notes)
            # to voice_rests(), while keeping leading whole rests before a 2-voice entry when barlines were missed.
            silent_voice_whole = (
                kind == 'block' and rest.get('hangs') and not rest.get('sits') and bool(bar_events)
                and (len(active_voices) == 1 or rest['x'] >= first_note_x)
            )
            if overlaps_note or silent_voice_whole:
                leftover.append(rest)
                continue
            free_rests.append(rest)

        # Pair vertically stacked rests at the same x-column into one shared rest column.
        paired: set[int] = set()
        candidates: list[tuple[float, int, int]] = []
        for i in range(len(free_rests)):
            mi = float(free_rests[i].get('middle', 0.0))
            for j in range(i + 1, len(free_rests)):
                mj = float(free_rests[j].get('middle', 0.0))
                if abs(mi - mj) >= 1.5 and (abs(mi) >= 0.75 or abs(mj) >= 0.75):
                    dx = abs(float(free_rests[i]['x']) - float(free_rests[j]['x']))
                    if dx <= 0.8 * space:
                        candidates.append((dx, i, j))
        candidates.sort()
        for _, i, j in candidates:
            if i in paired or j in paired:
                continue
            paired.add(i)
            paired.add(j)
            r_up, r_dn = (free_rests[i], free_rests[j]) if float(free_rests[i].get('middle', 0.0)) < float(free_rests[j].get('middle', 0.0)) else (free_rests[j], free_rests[i])
            rx = 0.5 * (float(r_up['x']) + float(r_dn['x']))
            len_up = _rest_length(r_up, not bar_events, bar_beats)
            len_dn = _rest_length(r_dn, not bar_events, bar_beats)
            rest_col = [
                {'x': rx, 'place': 0, 'voice': 1, 'head': {}, 'length': len_up, 'stem_x': None, 'rest': True},
                {'x': rx, 'place': 0, 'voice': 2, 'head': {}, 'length': len_dn, 'stem_x': None, 'rest': True},
            ]
            bar_map.setdefault(m_idx, []).append(rest_col)

        # Insert remaining unpaired non-overlapping rests when centered, in empty bars, or unspanned.
        for idx, rest in enumerate(free_rests):
            if idx in paired:
                continue
            kind = rest.get('kind', 'quarter')
            middle = float(rest.get('middle', 0.0))
            shifted = (kind in ('quarter', 'eighth', '16th') and abs(middle) >= 0.75) or (
                kind == 'block' and abs(middle) >= 1.15)
            length = _rest_length(rest, not bar_events, bar_beats)

            if not bar_events:
                # Keep whole, half, quarter, eighth, and 16th rests in empty or anacrusis bars.
                rv = (1 if middle < 0 else 2) if shifted else 1
                bar_map.setdefault(m_idx, []).append([
                    {'x': float(rest['x']), 'place': 0, 'voice': rv, 'head': {},
                     'length': length, 'stem_x': None, 'rest': True}
                ])
                continue

            if not shifted:
                rest_col = [{'x': float(rest['x']), 'place': 0, 'voice': v, 'head': {},
                             'length': length, 'stem_x': None, 'rest': True} for v in active_voices]
                bar_map[m_idx].append(rest_col)
                continue

            # Single shifted rest with no overlapping note: insert when no other voice spans across it.
            rv = 1 if middle < 0 else 2
            first_x = min(ev['x'] for ev in bar_events)
            last_x = max(ev['x'] for ev in bar_events)
            if rest['x'] < first_x:
                if len(active_voices) == 2:
                    first_col = min((col for col in bar_map[m_idx] if any(not ev.get('rest') for ev in col)),
                                    key=lambda c: c[0]['x'])
                    first_voices = {ev['voice'] for ev in first_col if not ev.get('rest')}
                    if rv not in first_voices:
                        # The other voice enters at the start of the bar while rv rests; keep in voice_rests().
                        leftover.append(rest)
                        continue
                voices_here = active_voices if len(active_voices) == 1 else [rv]
                bar_map[m_idx].append([
                    {'x': float(rest['x']), 'place': 0, 'voice': v, 'head': {},
                     'length': length, 'stem_x': None, 'rest': True} for v in voices_here
                ])
                continue

            if len(active_voices) == 1:
                if kind == 'block' and first_x < rest['x'] < last_x:
                    xs = sorted(ev['x'] for ev in bar_events)
                    steps = sorted(b - a for a, b in zip(xs, xs[1:]) if b - a > 0.3 * space)
                    left = [x for x in xs if x < rest['x0'] - 0.5 * space]
                    right = [x for x in xs if x > rest['x1'] + 0.5 * space]
                    even = bool(left and right and steps) and right[0] - left[-1] <= ALONE_STEP * steps[len(steps) // 2]
                    if even:
                        leftover.append(rest)
                        continue
                bar_map[m_idx].append([
                    {'x': float(rest['x']), 'place': 0, 'voice': v, 'head': {},
                     'length': length, 'stem_x': None, 'rest': True} for v in active_voices
                ])
                continue

            # Two-voice bar after the first note: route to voice_rests() when the other voice spans across
            # this rest or enters next without rv (so build_staff() does not push the other voice forward).
            free = _voice_free_before(bar_map[m_idx], float(rest['x']))
            other = 3 - rv
            next_note_cols = [col for col in sorted(bar_map[m_idx], key=lambda c: c[0]['x'])
                              if col[0]['x'] > float(rest['x']) and any(not ev.get('rest') for ev in col)]
            next_other_only = bool(next_note_cols) and {ev['voice'] for ev in next_note_cols[0] if not ev.get('rest')} == {other}
            if free[other] > free[rv] or (next_other_only and free[other] <= free[rv]):
                leftover.append(rest)
            else:
                bar_map[m_idx].append([
                    {'x': float(rest['x']), 'place': 0, 'voice': rv, 'head': {},
                     'length': length, 'stem_x': None, 'rest': True}
                ])

        if m_idx in bar_map:
            bar_map[m_idx].sort(key=lambda col: col[0]['x'])

    updated = [bar_map[k] for k in sorted(bar_map)]
    return updated, leftover


def read_page(grey: np.ndarray, places: list[dict], title: str = '', key_before: int | None = None,
              clefs_before: list[str] | None = None, key_hymn: int | None = None, ties_before: list | None = None,
              layers: dict | None = None, meter_before: tuple | None = None) -> dict:
    """Reads a clean page (a grey image and the places from clean_page()). Returns {'musicxml': text, 'notes': [...],
    'staves': n, 'systems': n, 'key': n, 'clefs': [...], 'layers': the layers}, and what was found on the way
    ('heads', 'bars', 'starts', 'ends', 'signs', 'note_signs', 'keys', 'ties', 'times', 'rests', 'fermatas') for pictures and
    checks.
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
                'keys': [], 'staff_keys': [], 'ties': [], 'words': [], 'triplets': [], 'rests': [], 'fermatas': [], 'times': []}
    if layers is None:
        layers = read_layers(grey, places)
        # The rows of the words: a stem ends where they begin, and a letter under a head is no stem.
        layers['words'] = word_bands(layers)
    words = layers['words']
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
    raw_bars = {index: list(xs) for index, xs in bars.items()}
    # A stem can cross the whole staff as a bar line does, but a head hangs on it.
    for index in bars:
        stems = [stem['x'] for head in heads if head['staff'] == index for stem in head['stems']]
        bars[index] = [x for x in bars[index] if all(abs(x - stem) > 0.4 * space for stem in stems)]
    # A stem from a head at an outer line crosses the staff as a bar line does, and the head's inside stands beside it.
    bar_stems_dropped = bar_stems(layers, bars, ends)
    for index, found in bar_stems_dropped.items():
        bars[index] = [x for x in bars[index] if x not in found]
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
    # A head read from its stem at one arc of an open ring is the whole ring, where no inside was read there.
    heads = ring_heads(heads)
    # A whole note in the space next to the staff that was left as two bold arcs.
    heads += arc_wholes(layers, heads, ends)
    # A whole note in the staff or on a ledger line that was left as two short bold strokes.
    heads += arc_pairs(layers, heads, ends)
    # A whole note whose thin rim broke, read from its open inside.
    broken = open_wholes(layers, heads, ends)
    gone = {id(other) for head in broken for other in head.get('replaces', [])}
    heads = [head for head in heads if id(head) not in gone] + broken
    # The numbers of a new time signature are no notes.
    times = mid_signs(layers, ends, bars) if TIMES else {}
    if TIMES:
        heads = [head for head in heads if not any(sign['x0'] - 0.2 * space <= head['cx'] <= sign['x1'] + 0.2 * space
                                                   and (not sign.get('bold') or abs(head['cy'] - staves[head['staff']]['rows'][2])
                                                        <= COMMON_ROWS * staves[head['staff']]['space'])
                                                   for sign in times[head['staff']])]
    if TIMES and TIME_COLUMN:
        heads = [head for head in heads if not other_time(head, staves, begin['starts'], times, space)]
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
    # A stem that stops short of a staff line, which a slur along it keeps in the ink, ends before the line.
    line_gap_stems(layers, heads)
    # A stem that breaks off before its beam ends at the beam.
    broken_stems(layers, heads)
    count_tails(layers, heads)
    loops_have_flags(layers, heads)
    # A hollow mark whose inside stands upright is the loop of a flag or the room of a double bar line, no head.
    heads = without_upright_holes(layers, heads)
    heads = without_flag_loops(heads, space)
    heads = without_flat_cells(layers, heads)
    heads = without_clip_cells(layers, heads)
    heads = without_grey_marks(layers, heads)
    heads = without_flag_trails(layers, heads)
    heads = without_flag_curls(heads, space)
    heads = without_flag_strokes(heads, space)
    heads = without_stem_end_marks(layers, heads)
    heads = without_top_loops(layers, heads)
    heads = without_far_marks(layers, heads)
    heads = without_stem_spans(layers, heads)
    heads = without_beam_pieces(layers, heads)
    heads = without_bow_middles(layers, heads)
    # A mark that hangs on a line of the system is a head only by its own shape: no stem goes on through the next staff.
    heads = without_line_marks(layers, heads, bars)
    # The letters of the dynamics: the paper between the two letters of an ff is no head, and the bowl of a p is no
    # whole note.
    heads = without_f_marks(layers, heads)
    heads = without_p_bowls(layers, heads)
    # A letter of a row of words beside the staff (a heading, a short row right over the staff) is no whole note.
    heads = without_row_letters(layers, heads)
    heads = without_stem_meets(layers, heads)
    # A column of printed dots is no head: its top dot was read with the others as its stem.
    heads = without_dot_columns(layers, heads)
    # A grace note is no note of the bar: the marks that were read from it go, and it is written before the next note
    # of its staff (scorereader.symbols.GRACE).
    heads, graces = grace_notes(layers, heads)
    # A fermata is no note: the thick middle of its arc was read as a flat head, with an arm of the arc as its stem.
    holds = fermatas(layers)
    heads = [head for head in heads if not on_fermata(head, holds, space)]
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
    # Local offline neural verification (SymNet) before tie reading and barline restoration so
    # phantom tie-crossing marks do not block barline ties or suppress true barlines.
    neural_on = headnet.weights() is not None
    sym_w = classify.load_weights() if neural_on else None
    if sym_w is not None and heads:
        pts = [(h['staff'], float(h['cx']), float(h['cy'])) for h in heads]
        probs_all = classify.classify_points(layers, pts, sym_w)
        kept_heads = []
        for head, probs in zip(heads, probs_all):
            head['symnet'] = probs
            p_head = float(probs[0] + probs[1] + probs[2] + probs[3])
            p_filled, p_hollow = float(probs[0]), float(probs[1])
            p_whole, p_breve = float(probs[2]), float(probs[3])
            # Reject high-confidence non-heads (dynamics, rests, fermatas, bar-crossing marks); require
            # stricter rejection for stemmed hollow heads with clear interior holes.
            hole = float(head.get('hole', 0.0) or 0.0)
            drop_thr = 0.015 if (head['stems'] and head['hollow'] and hole >= 0.15) else 0.05
            if p_head < drop_thr and not head.get('dot'):
                continue
            # Flip filled <-> hollow on stemmed heads only when visual ink cues do not contradict SymNet.
            if head['stems']:
                has_tails = any(head.get('tails', {}).values()) or bool(head.get('flag_ink'))
                if head['hollow']:
                    if has_tails and p_filled >= 0.85 and p_hollow <= 0.10:
                        head['hollow'] = False
                        head['net_flip'] = True
                    elif not has_tails and hole < 0.20 and p_filled >= 0.92 and p_hollow <= 0.05:
                        head['hollow'] = False
                        head['net_flip'] = True
                    elif not has_tails and hole < 0.28 and p_filled >= 0.98 and p_hollow <= 0.01:
                        head['hollow'] = False
                        head['net_flip'] = True
                elif not has_tails and ((hole > 0.0 or head.get('slit')) and p_hollow >= 0.90 and p_filled <= 0.08
                                        or p_hollow >= 0.96 and p_filled <= 0.02):
                    head['hollow'] = True
                    head['net_flip'] = True
            elif head['hollow'] and p_hollow >= 0.92 and p_whole <= 0.03 and p_breve <= 0.03:
                # A dotted stemless hollow head classified as a half note had its stem lost;
                # undotted stemless hollow heads convert only in multi-column bars (protecting solo whole notes).
                if head.get('dot'):
                    head['half_stemless'] = True
                else:
                    head['half_stemless_multi'] = True
                head['net_flip'] = True
            kept_heads.append(head)
        heads = kept_heads

    # Restore barlines that were suppressed only by phantom heads later removed by filters or SymNet.
    for index, raw_xs in raw_bars.items():
        if not raw_xs:
            continue
        cur_xs = bars.get(index, [])
        dropped_stems = set(bar_stems_dropped.get(index, ()))
        surv_heads = [h for h in heads if h['staff'] == index]
        surv_stems = [s['x'] for h in surv_heads for s in h['stems']]
        restored = []
        for bx in raw_xs:
            if bx in dropped_stems or bx <= ends[index] + 0.5 * space:
                continue
            if any(abs(bx - cx) <= 0.4 * space for cx in cur_xs):
                continue
            if any(abs(bx - sx) <= 0.4 * space for sx in surv_stems):
                continue
            if any(h['x0'] - 0.2 * space <= bx <= h['x1'] + 0.2 * space for h in surv_heads):
                continue
            restored.append(bx)
        if restored:
            bars[index] = sorted(cur_xs + restored)

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
    kept = without_breves(layers, heads, letters)
    letters = start_breves(layers, heads, kept, letters)
    heads = kept

    stem_w = classify.load_stem_weights() if neural_on else None
    if stem_w is not None and heads:
        stem_items = []
        stem_refs = []
        for head in heads:
            if head['hollow'] or not head['stems']:
                continue
            for stem in head['stems']:
                stem_items.append((head['staff'], float(stem['x']), float(stem['end']), stem['direction']))
                stem_refs.append((head, stem))
        if stem_items:
            s_probs = classify.classify_stems(layers, stem_items, stem_w)
            for (head, stem), sp in zip(stem_refs, s_probs):
                stem['stemnet'] = sp
                direction = stem['direction']
                cur_t = head.get('tails', {}).get(direction, 0)
                marks = stem.get('marks', [])
                unwitnessed = any(m.get('beam') and not m.get('witness') for m in marks)
                has_beam_mark = any(m.get('beam') for m in marks)
                if cur_t == 0 and not unwitnessed and float(sp[1]) >= 0.95 and float(sp[0]) <= 0.04:
                    head.setdefault('tails', {})[direction] = 1
                    head['stemnet_flip'] = True
                elif cur_t == 1 and (stem.get('beam_only') or unwitnessed) and float(sp[0]) >= 0.93 and float(sp[1]) <= 0.05 and not head.get('triplet'):
                    # Only hard-downgrade weak or unwitnessed beam marks before grammar; preserve real flags and witnessed beams.
                    head.setdefault('tails', {})[direction] = 0
                    head['stemnet_flip'] = True
                elif cur_t == 1 and float(sp[2]) >= 0.93 and float(sp[1]) <= 0.05:
                    head.setdefault('tails', {})[direction] = 2
                    head['stemnet_flip'] = True
                elif cur_t == 2 and has_beam_mark and float(sp[1]) >= 0.94 and float(sp[2]) <= 0.04:
                    # Only hard-downgrade spurious double-beam marks; preserve printed double flags.
                    head.setdefault('tails', {})[direction] = 1
                    head['stemnet_flip'] = True

    # Detect printed eighth and sixteenth rests plus optional neural rest candidates, then apply rest dots.
    short_rests = eighth_rests(layers, ends, heads, bars)
    all_rests = rests + blocks + short_rests
    neural_rests_fn = getattr(_rests_mod, 'neural_rest_candidates', None)
    if neural_rests_fn is not None and neural_on:
        all_rests = all_rests + neural_rests_fn(layers, ends, heads, bars, all_rests, weights=sym_w)
    for rest in all_rests:
        base_len = Fraction(rest.get('length', 1))
        if base_len in (Fraction(2), Fraction(1), Fraction(1, 2)) and rest_dot(layers, rest):
            rest['length'] = base_len * Fraction(3, 2)
            rest['dot'] = True
    opening_meter, meter_changes = page_meter(layers, begin['starts'], times, ends)
    effective_meter = opening_meter or meter_before
    parts = [[] for _ in range(width)]
    notes, part_notes = [], []
    plans = {index: staff_columns(staff, [head for head in heads if head['staff'] == index], bars[index], space)
             for index, staff in enumerate(staves)}
    # Infer an opening meter on excerpt pages that have mid-page meter changes and no printed opening meter.
    infer_fn = getattr(_meter_mod, 'infer_opening_meter', None)
    if opening_meter is None and meter_before is None and meter_changes and infer_fn is not None:
        first_change_sys = min(staves[idx]['system'] for idx in meter_changes)
        pre_sys_ids = sorted({staff['system'] for staff in staves if staff['system'] < first_change_sys})
        if not pre_sys_ids:
            pre_sys_ids = sorted({staff['system'] for staff in staves})
        pre_sums = [
            value
            for sys_id in pre_sys_ids
            for value in bar_sums({idx: plans[idx] for idx, st in enumerate(staves) if st['system'] == sys_id},
                                  bars, space, rests)
        ]
        inferred = infer_fn(pre_sums)
        if inferred is not None:
            opening_meter = inferred
            effective_meter = inferred
    bar_beats = Fraction(effective_meter[0] * 4, effective_meter[1]) if effective_meter else None
    # Attach StemNet probabilities to plan events for the global music-grammar solver.
    for plan in plans.values():
        for bar in plan:
            for col in bar:
                for ev in col:
                    head = ev.get('head') or {}
                    direction = 'up' if ev.get('voice') == 1 else 'down'
                    st_match = next((s for s in head.get('stems', []) if s['direction'] == direction), None)
                    if st_match is not None and st_match.get('stemnet') is not None:
                        ev['stemnet'] = st_match['stemnet']
    # Music check: the voices of a system agree on the length of each step from column to column.
    agreed = 0
    if CHECK:
        sys_ids = sorted({staff['system'] for staff in staves})
        systems = [{index: plans[index] for index, staff in enumerate(staves) if staff['system'] == system}
                   for system in sys_ids]
        # The sum that most bars of the page have: a bar with one open step is as long (scorereader.music.BAR_FULL).
        # On a page whose bars keep their length, a bar that is too long is looked at too (scorereader.music.BAR_OVER).
        sums = [value for own in systems for value in bar_sums(own, bars, space, rests)]
        full, steady = full_sum(sums), full_sum(sums, _music.BAR_OVER) if _music.BAR_OVER else None
        cur_sys_meter = effective_meter
        for sys_idx, own in zip(sys_ids, systems):
            agreed += agree_lengths(own, bars, space, rests, full, steady)
            sys_changes = {idx: meter_changes[idx] for idx in own if idx in meter_changes}
            agreed += _grammar.solve_system_durations(
                own, bars, space, all_rests, cur_sys_meter,
                is_first_system=(sys_idx == 0), meter_changes=sys_changes or None,
            )
            if sys_changes:
                last_ch = max((item for chs in sys_changes.values() for item in chs), key=lambda item: item[0])
                cur_sys_meter = last_ch[1]
    # The ison of a chant page (one staff for the melody): the letters over the staff name its note (scorereader.drone).
    # It is a part of its own after the melody; its notes are in no list of notes, so no syllable is set under them.
    drone, holding = [], {}
    places = voice_places(staves, plans) if REST_VOICE else {}
    for index, staff in enumerate(staves):
        staff_rests = [r for r in all_rests if r['staff'] == index]
        # Exclude blocks trapped between stems (ties printed into staff lines).
        if REST_APART is not None:
            note_stub = [{'head': ev['head']} for bar in plans[index] for col in bar for ev in col if ev.get('head')]
            staff_rests = [r for r in staff_rests if r.get('kind') != 'block' or not _between_stems(r, note_stub, space)]
        plan_with_rests, leftover_rests = _insert_shared_rests(staff, plans[index], bars[index], staff_rests, space, bar_beats)
        built = build_staff(staff, [], bars[index], clefs[index], keys[index], space, plan_with_rests)
        if width == 1 and built:
            marks = [[] for _ in built]
            for mark in letters[index]:
                later = [number for number, bar in enumerate(plan_with_rests) if any(column[0]['x'] >= mark['x'] - 0.6 * space for column in bar)]
                marks[later[0] if later else len(built) - 1].append(mark)

            def pitch(event: dict, staff=staff, index=index) -> dict:
                return build_staff(staff, [], [], clefs[index], keys[index], space, [[[dict(event, voice=1)]]])[0][0]

            for bar in held(built, marks, pitch, space, holding):
                drone.append({'notes': [{name: value for name, value in note.items() if name != 'head'} for note in bar],
                              'clef': clefs[index], 'key': keys[index]})
        quiet = voice_rests(staff, built, plan_with_rests, bars[index], leftover_rests, space,
                            places.get(staff['number'])) if REST_VOICE else {}
        first = len(parts[staff['number']])
        staff_edges = [x for x in sorted(bars[index]) if staff['x0'] + 2 * space < x < staff['x1'] - space]
        change_bars = {sum(1 for x in staff_edges if x < cx): m for cx, m in meter_changes.get(index, [])}
        active_bar_meter = effective_meter
        for number, bar in enumerate(built):
            bar_entry = {'notes': bar, 'clef': clefs[index], 'key': keys[index]}
            if opening_meter is not None and staff['system'] == 0 and number == 0:
                bar_entry['time'] = opening_meter
                active_bar_meter = opening_meter
            elif number in change_bars:
                bar_entry['time'] = change_bars[number]
                active_bar_meter = change_bars[number]
            parts[staff['number']].append(bar_entry)
            if quiet.get(number):
                parts[staff['number']][-1]['rests'] = quiet[number]
            bar_target = Fraction(active_bar_meter[0] * 4, active_bar_meter[1]) if active_bar_meter else None
            bar_end = max((item['onset'] + item['length'] for item in bar), default=Fraction(0))
            bar_sum_ok = (bar_end == bar_target) if (bar_target is not None and bar) else None
            for note in bar:
                if note.get('rest'):
                    continue
                head = note.pop('head')
                part_notes.append(note)
                stem = next((s for s in head['stems'] if (s['direction'] == 'up') == (note['voice'] == 1)), None)
                conf = _grammar.note_confidence(note, head, stem, bar_sum_ok=bar_sum_ok)
                notes.append(dict(note, staff=index, bar=number, onset=float(note['onset']), length=float(note['length']),
                                  agreed=note.get('agreed', False), votes=note.get('votes'), confidence=conf,
                                  mark={'wide': int(head['x1'] - head['x0'] + 1), 'high': int(head['y1'] - head['y0'] + 1),
                                        'y': float(head['cy']), 'at': float(head['place']), 'hollow': bool(head['hollow']),
                                        'hole': float(head.get('hole', 0)), 'core': head.get('core'), 'alt': head.get('alt'), 'thin': bool(head.get('thin')), 'dot': bool(head.get('dot')), 'triplet': bool(head.get('triplet')),
                                        'sign': head.get('sign'), 'stems': [s['direction'] for s in head['stems']],
                                        'stem': {'x': float(stem['x']), 'end': float(stem['end']), 'tails': head['tails'].get(stem['direction'], 0),
                                                 'marks': stem.get('marks', [])} if stem else None}))
        for grace in (grace for grace in graces if grace['staff'] == index):
            later = [(number, note) for number, bar in enumerate(built) for note in bar
                     if not note.get('rest') and note['x'] > grace['cx']]
            if not later:
                continue
            number, note = min(later, key=lambda item: (item[1]['x'], -item[1]['midi']))
            place = int(round(grace['place']))
            step, alter, octave, midi = pitch_of(place, clefs[index], key_alters(keys[index]).get((MIDDLE[clefs[index]] + place) % 7, 0))
            parts[staff['number']][first + number].setdefault('graces', []).append(
                {'onset': note['onset'], 'voice': note['voice'], 'step': step, 'alter': alter, 'octave': octave, 'midi': midi,
                 'x': float(grace['cx'])})
            grace.update(step=step, alter=alter, octave=octave, bar=number)
    names = {}
    if any(bar['notes'] for bar in drone):
        parts.append(drone)
        names[width] = 'Ison'
    # The notes are read: the step of the words gets the rows that stand staggered too.
    words = layers['words'] = word_rows(layers)
    return {'musicxml': musicxml(parts, title, names), 'parts': parts, 'names': names, 'notes': notes, 'part_notes': part_notes, 'title': title,
            'staves': len(staves), 'systems': len({staff['system'] for staff in staves}), 'key': key, 'clefs': clefs, 'layers': layers,
            'meter': effective_meter, 'opening_meter': opening_meter,
            'system_clefs': [system_clefs[number] for number in sorted(system_clefs)],
            'ties_out': [[staves[head['staff']]['number'], int(round(head['place']))] for head in heads if head.get('tie_out')],
            'heads': heads, 'note_signs': found, 'starts': begin['starts'], 'ends': ends, 'bars': bars, 'signs': symbols['signs'],
            'keys': [start['key'] for start in begin['starts']], 'staff_keys': keys, 'ties': ties, 'words': words, 'triplets': triplets,
            'rests': all_rests, 'fermatas': holds, 'times': [([start['time']] if start.get('time') else []) + times.get(index, [])
                      for index, start in enumerate(begin['starts'])]}

#!/usr/bin/env python3
"""Honest evaluator for scoreread: Note F1, Precision, Recall, Rest F1, Onsets, and Time Signatures.

Unlike recall-only scorers, this script penalizes phantom ("extra") notes directly inside Precision and F1,
scores rests and time signatures, and checks note onset timing.

Usage:
  python3 bench/eval_f1.py --manifest out/eval/clean_dev.json --results out/eval/baseline_dev
  python3 bench/eval_f1.py --kit "$SCOREREAD_KIT" --results out/kit --tool own --kind printed
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from fractions import Fraction
from pathlib import Path

STEPS = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
NAMES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']


def frac(value) -> Fraction:
    """Converts a beat position or duration to an exact fraction."""
    return Fraction(value).limit_denominator(192)


def note_name(midi: int) -> str:
    return f'{NAMES[midi % 12]}{midi // 12 - 1}'


def musicxml_root(path: Path) -> ET.Element:
    if path.suffix.lower() == '.mxl':
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            inner = next((n for n in names if n.lower().endswith(('.xml', '.musicxml')) and not n.startswith('META-INF')), None)
            if inner is None:
                raise ValueError('archive holds no MusicXML file')
            data = archive.read(inner)
    else:
        data = path.read_bytes()
    root = ET.fromstring(data)
    for element in root.iter():
        if isinstance(element.tag, str) and '}' in element.tag:
            element.tag = element.tag.split('}', 1)[1]
    return root


def read_musicxml(path: Path) -> dict:
    """Reads notes, rests, and time signatures for each staff of a MusicXML file."""
    root = musicxml_root(path)
    staves_notes: list[list[dict]] = []
    staves_rests: list[list[dict]] = []
    meters: list[str] = []
    length = Fraction(0)
    for part in root.findall('part'):
        divisions = 1
        start = Fraction(0)
        by_staff_notes: dict[int, list[dict]] = {}
        by_staff_rests: dict[int, list[dict]] = {}
        count = 1
        clefs: dict[int, str] = {}
        for measure in part.findall('measure'):
            position = Fraction(0)
            furthest = Fraction(0)
            last_onset = Fraction(0)
            for element in measure:
                tag = element.tag
                if tag == 'attributes':
                    value = element.findtext('divisions')
                    if value:
                        divisions = max(1, int(round(float(value))))
                    value = element.findtext('staves')
                    if value:
                        count = max(count, int(value))
                    for clef in element.findall('clef'):
                        sign = (clef.findtext('sign') or '').strip().upper()
                        if sign:
                            clefs[int(clef.get('number') or 1)] = sign
                    for time_el in element.findall('time'):
                        symbol = time_el.get('symbol')
                        beats = (time_el.findtext('beats') or '').strip()
                        btype = (time_el.findtext('beat-type') or '').strip()
                        if symbol == 'common':
                            meters.append('C')
                        elif symbol == 'cut':
                            meters.append('C|')
                        elif beats and btype:
                            meters.append(f'{beats}/{btype}')
                elif tag in ('backup', 'forward'):
                    step = Fraction(int(round(float(element.findtext('duration') or 0))), divisions)
                    position = position - step if tag == 'backup' else position + step
                    furthest = max(furthest, position)
                elif tag == 'note':
                    if element.find('grace') is not None:
                        continue
                    duration = Fraction(int(round(float(element.findtext('duration') or 0))), divisions)
                    if element.find('chord') is not None:
                        onset = last_onset
                    else:
                        onset = position
                        last_onset = position
                        position += duration
                        furthest = max(furthest, position)
                    if element.find('cue') is not None or element.get('print-object') == 'no':
                        continue
                    staff = int(element.findtext('staff') or 1)
                    count = max(count, staff)
                    voice = (element.findtext('voice') or '1').strip()
                    if element.find('rest') is not None:
                        by_staff_rests.setdefault(staff, []).append({
                            'on': frac(start + onset), 'len': frac(duration), 'voice': voice,
                        })
                        continue
                    pitch = element.find('pitch')
                    if pitch is None:
                        continue
                    midi = (12 * (int(pitch.findtext('octave')) + 1)
                            + STEPS[pitch.findtext('step').strip().upper()]
                            + int(round(float(pitch.findtext('alter') or 0))))
                    ties = [t.get('type') for t in element.findall('tie')]
                    ties += [t.get('type') for t in element.findall('notations/tied')]
                    by_staff_notes.setdefault(staff, []).append({
                        'on': frac(start + onset), 'len': frac(duration), 'midi': midi,
                        'voice': voice, 'tie_start': 'start' in ties, 'tie_stop': 'stop' in ties,
                        'clef': clefs.get(staff, 'G'),
                    })
            start += max(furthest, position)
        length = max(length, start)
        for staff in range(1, count + 1):
            staves_notes.append(by_staff_notes.get(staff, []))
            staves_rests.append(by_staff_rests.get(staff, []))
    return {'notes': staves_notes, 'rests': staves_rests, 'meters': meters, 'length': length}


def join_ties(notes: list[dict]) -> list[dict]:
    """Joins consecutive tied notes of one pitch into a single note with summed duration."""
    joined: list[dict] = []
    open_ties: list[dict] = []
    for note in sorted(notes, key=lambda n: (n['on'], -n['midi'])):
        if note['tie_stop']:
            ends_here = [b for b in open_ties if b['midi'] == note['midi'] and b['on'] + b['len'] == note['on']]
            before = next((t for t in ends_here if t['voice'] == note['voice']), ends_here[0] if ends_here else None)
            if before is not None:
                before['len'] += note['len']
                if not note['tie_start']:
                    open_ties.remove(before)
                continue
        copy = dict(note)
        joined.append(copy)
        open_ties = [t for t in open_ties if t['on'] + t['len'] >= copy['on']]
        if copy['tie_start']:
            open_ties.append(copy)
    return joined


def read_case_outputs(folder: Path, case: dict) -> dict:
    """Loads per-page MusicXML outputs (or joined hymn output) for one score."""
    staves_notes: list[list[dict]] = []
    staves_rests: list[list[dict]] = []
    meters: list[str] = []
    offset = Fraction(0)
    pages = case.get('page_stems') or [f"{case['id']}-p{p}" for p in case['pages']]
    found_pages = 0
    for stem in pages:
        candidates = sorted(p for p in folder.glob(f'{stem}.*') if p.suffix.lower() in ('.musicxml', '.xml', '.mxl'))
        plain = [p for p in candidates if p.suffix.lower() != '.mxl']
        chosen = plain or candidates
        if not chosen:
            continue
        found_pages += 1
        page_len = Fraction(0)
        for path in chosen:
            try:
                parsed = read_musicxml(path)
            except Exception:
                continue
            meters.extend(parsed['meters'])
            for idx, notes in enumerate(parsed['notes']):
                while len(staves_notes) <= idx:
                    staves_notes.append([])
                staves_notes[idx].extend(dict(n, on=n['on'] + offset + page_len) for n in notes)
            for idx, rests in enumerate(parsed['rests']):
                while len(staves_rests) <= idx:
                    staves_rests.append([])
                staves_rests[idx].extend(dict(r, on=r['on'] + offset + page_len) for r in rests)
            page_len += parsed['length']
        offset += page_len
    return {
        'notes': [join_ties(s) for s in staves_notes],
        'rests': staves_rests,
        'meters': meters,
        'found_pages': found_pages,
        'expected_pages': len(pages),
    }


def split_by_clef(staves: list[list[dict]], wanted: int) -> list[list[dict]]:
    if len(staves) >= wanted:
        return staves
    out: list[list[dict]] = []
    for idx, notes in enumerate(staves):
        lower = [n for n in notes if n.get('clef') == 'F']
        upper = [n for n in notes if n.get('clef') != 'F']
        after = len(staves) - idx - 1
        if len(out) + 2 + after <= wanted and min(len(lower), len(upper)) >= 0.1 * len(notes):
            out.extend([upper, lower])
        else:
            out.append(notes)
    return out


def reader_tokens(notes: list[dict]) -> list[tuple]:
    seen = set()
    tokens = []
    for n in notes:
        key = (n['on'], n['len'], n['midi'])
        if key not in seen:
            seen.add(key)
            tokens.append(key + (n['voice'],))
    return sorted(tokens, key=lambda t: (t[0], -t[2]))


def truth_tokens(truth: dict, parts: list[str], pick: str | None = None) -> list[tuple]:
    seen = set()
    tokens = []
    for part in parts:
        for n in truth['parts'].get(part, []):
            pitches = n['midi'] if pick is None else [max(n['midi']) if pick == 'top' else min(n['midi'])]
            for midi in pitches:
                key = (frac(n['at']), frac(n['len']), midi)
                if key not in seen:
                    seen.add(key)
                    tokens.append(key)
    return sorted(tokens, key=lambda t: (t[0], -t[2]))


def truth_rests(truth: dict, parts: list[str]) -> list[tuple]:
    """Returns unique rest intervals (onset, length) across the given parts."""
    seen = set()
    rests = []
    for part in parts:
        explicit = truth.get('rests', {}).get(part)
        if explicit is not None:
            for r in explicit:
                key = (frac(r['at']), frac(r['len']))
                if key not in seen and key[1] > 0:
                    seen.add(key)
                    rests.append(key)
        else:
            prev_end = Fraction(0)
            for n in sorted(truth['parts'].get(part, []), key=lambda x: frac(x['at'])):
                at, ln = frac(n['at']), frac(n['len'])
                if at > prev_end:
                    key = (prev_end, at - prev_end)
                    if key not in seen:
                        seen.add(key)
                        rests.append(key)
                prev_end = max(prev_end, at + ln)
    return sorted(rests, key=lambda r: (r[0], r[1]))


def align_notes(expected: list[tuple], actual: list[tuple]) -> tuple[float, list[tuple[int | None, int | None]]]:
    rows, cols = len(expected), len(actual)
    prev = [float(c) for c in range(cols + 1)]
    moves = [bytearray(cols + 1) for _ in range(rows + 1)]
    for c in range(1, cols + 1):
        moves[0][c] = 2
    for r in range(1, rows + 1):
        curr = [float(r)] + [0.0] * cols
        moves[r][0] = 1
        ln, p = expected[r - 1][1], expected[r - 1][2]
        line = moves[r]
        for c in range(1, cols + 1):
            oln, op = actual[c - 1][1], actual[c - 1][2]
            diag = prev[c - 1] + (0.5 if p != op else 0.0) + (0.5 if ln != oln else 0.0)
            up = prev[c] + 1.0
            left = curr[c - 1] + 1.0
            if diag <= up and diag <= left:
                curr[c] = diag
            elif up <= left:
                curr[c] = up
                line[c] = 1
            else:
                curr[c] = left
                line[c] = 2
        prev = curr
    pairs = []
    r, c = rows, cols
    while r or c:
        m = moves[r][c]
        if r and c and m == 0:
            pairs.append((r - 1, c - 1))
            r -= 1
            c -= 1
        elif r and (m == 1 or not c):
            pairs.append((r - 1, None))
            r -= 1
        else:
            pairs.append((None, c - 1))
            c -= 1
    pairs.reverse()
    return prev[cols], pairs


def align_rests(expected: list[tuple], actual: list[tuple]) -> tuple[int, int, int]:
    """Aligns rest durations via edit distance and returns (matched_exact, expected_count, actual_count)."""
    rows, cols = len(expected), len(actual)
    if rows == 0 or cols == 0:
        return 0, rows, cols
    dp = [[0] * (cols + 1) for _ in range(rows + 1)]
    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            if expected[r - 1][1] == actual[c - 1][1]:
                dp[r][c] = dp[r - 1][c - 1] + 1
            else:
                dp[r][c] = max(dp[r - 1][c], dp[r][c - 1])
    return dp[rows][cols], rows, cols


def match_staves(expected_staves: list[list[tuple]], actual_staves: list[list[tuple]]) -> list[int | None]:
    costs = [[align_notes(exp, act)[0] for act in actual_staves] for exp in expected_staves]
    none_penalty = max((len(a) for a in actual_staves), default=0) + 1
    choices = list(range(len(actual_staves))) + [None] * len(expected_staves)
    best, best_key = None, None
    for chosen in set(itertools.permutations(choices, len(expected_staves))):
        used = [i for i in chosen if i is not None]
        if len(used) != len(set(used)):
            continue
        cost = sum(costs[r][i] if i is not None else len(expected_staves[r]) + none_penalty
                   for r, i in enumerate(chosen))
        key = (cost, [i if i is not None else 99 for i in chosen])
        if best_key is None or key < best_key:
            best, best_key = chosen, key
    return list(best) if best else [None] * len(expected_staves)


def split_parts(tokens: list[tuple]) -> tuple[list[tuple], list[tuple]]:
    counts: dict[str, int] = {}
    for tok in tokens:
        counts[tok[3]] = counts.get(tok[3], 0) + 1
    voices = [v for v, cnt in counts.items() if cnt >= 0.1 * len(tokens)]
    upper: list[tuple] = []
    lower: list[tuple] = []
    ends: dict[str, Fraction | None] = {'upper': None, 'lower': None}

    def busy(part: str, onset: Fraction) -> bool:
        return ends[part] is not None and ends[part] > onset

    def put(part: str, tok: tuple, onset: Fraction) -> None:
        (upper if part == 'upper' else lower).append(tok)
        ends[part] = onset + tok[1]

    if len(voices) == 2:
        mean = {v: sum(t[2] for t in tokens if t[3] == v) / counts[v] for v in voices}
        high_v, low_v = sorted(voices, key=lambda v: -mean[v])
        for onset, grp in itertools.groupby(tokens, key=lambda t: t[0]):
            grp_list = list(grp)
            high = [t for t in grp_list if t[3] == high_v]
            low = [t for t in grp_list if t[3] == low_v]
            rest = [t for t in grp_list if t[3] not in voices]
            if not high and not low and rest:
                high, low = rest, []
            if high and low:
                put('upper', max(high, key=lambda t: t[2]), onset)
                put('lower', min(low, key=lambda t: t[2]), onset)
            elif high or low:
                chord = sorted(high or low, key=lambda t: -t[2])
                other = 'lower' if high else 'upper'
                own = 'upper' if high else 'lower'
                if len(chord) > 1:
                    put('upper', chord[0], onset)
                    put('lower', chord[-1], onset)
                else:
                    put(own, chord[0], onset)
                    if not busy(other, onset):
                        put(other, chord[0], onset)
        return upper, lower

    for onset, grp in itertools.groupby(tokens, key=lambda t: t[0]):
        chord = sorted(grp, key=lambda t: -t[2])
        if len(chord) > 1:
            put('upper', chord[0], onset)
            put('lower', chord[-1], onset)
            continue
        note = chord[0]
        ub, lb = busy('upper', onset), busy('lower', onset)
        if ub and not lb:
            put('lower', note, onset)
        elif lb and not ub:
            put('upper', note, onset)
        elif ub and lb:
            to_u = abs(note[2] - upper[-1][2]) <= abs(note[2] - lower[-1][2])
            put('upper' if to_u else 'lower', note, onset)
        else:
            put('upper', note, onset)
            put('lower', note, onset)
    return upper, lower


def norm_meter(m: str | None) -> str | None:
    if not m or m.lower() == 'none':
        return None
    m = m.strip()
    if m == 'C':
        return '4/4'
    if m == 'C|':
        return '2/2'
    return m


def tally_pairs(expected: list[tuple], actual: list[tuple], pairs: list[tuple[int | None, int | None]]) -> dict:
    c = {
        'expected': len(expected), 'read': len(actual), 'right': 0,
        'pitch_only': 0, 'len_only': 0, 'both_wrong': 0, 'missed': 0, 'extra': 0,
        'onset_exact': 0, 'dt_ok': 0, 'dt_total': 0,
    }
    len_conf: Counter = Counter()
    pitch_err: Counter = Counter()
    prev = None
    for r, k in pairs:
        if r is None:
            c['extra'] += 1
        elif k is None:
            c['missed'] += 1
        else:
            sp = expected[r][2] == actual[k][2]
            sl = expected[r][1] == actual[k][1]
            if sp and sl:
                c['right'] += 1
                if expected[r][0] == actual[k][0]:
                    c['onset_exact'] += 1
                if prev is not None:
                    c['dt_total'] += 1
                    if expected[r][0] - expected[prev[0]][0] == actual[k][0] - actual[prev[1]][0]:
                        c['dt_ok'] += 1
                prev = (r, k)
            elif not sp and sl:
                c['pitch_only'] += 1
                dp = actual[k][2] - expected[r][2]
                if abs(dp) == 1:
                    pitch_err['semitone'] += 1
                elif abs(dp) == 12:
                    pitch_err['octave'] += 1
                elif abs(dp) <= 4:
                    pitch_err['step_1_2'] += 1
                else:
                    pitch_err['large'] += 1
            elif sp and not sl:
                c['len_only'] += 1
                len_conf[f'{expected[r][1]}->{actual[k][1]}'] += 1
            else:
                c['both_wrong'] += 1
    c['len_conf'] = len_conf
    c['pitch_err'] = pitch_err
    return c


def prf(right: int, expected: int, read: int) -> tuple[float, float, float]:
    rec = right / expected if expected else 1.0
    prec = right / read if read else (1.0 if expected == 0 else 0.0)
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return prec, rec, f1


def score_case(folder: Path, case: dict, truth: dict) -> dict:
    out = read_case_outputs(folder, case)
    layout = case['layout']
    # When LitChoir displays ['melody', 'ison'] on one UI staff but the reader emits separate melody and ison parts,
    # score both parts directly instead of dropping the ison part.
    if layout == [['melody', 'ison']] and len(out['notes']) == 2:
        layout = [['melody'], ['ison']]
    staves = split_by_clef(out['notes'], len(layout))
    actual = [reader_tokens(s) for s in staves]
    expected = [truth_tokens(truth, parts) for parts in layout]
    chosen = match_staves(expected, actual)

    staff_sum = Counter()
    part_sum = Counter()
    len_conf = Counter()
    pitch_err = Counter()
    rest_matched = rest_exp = rest_act = 0

    for row, (parts, exp_tok) in enumerate(zip(layout, expected)):
        idx = chosen[row]
        rd = actual[idx] if idx is not None else []
        _, pairs = align_notes(exp_tok, rd)
        sc = tally_pairs(exp_tok, rd, pairs)
        for k, v in sc.items():
            if isinstance(v, int):
                staff_sum[k] += v
        len_conf.update(sc['len_conf'])
        pitch_err.update(sc['pitch_err'])

        # Rest scoring on this staff
        exp_r = truth_rests(truth, parts)
        act_r_raw = out['rests'][idx] if (idx is not None and idx < len(out['rests'])) else []
        seen_r = set()
        act_r = []
        for r in act_r_raw:
            key = (r['on'], r['len'])
            if key not in seen_r and r['len'] > 0:
                seen_r.add(key)
                act_r.append(key)
        act_r.sort()
        rm, re_n, ra_n = align_rests(exp_r, act_r)
        rest_matched += rm
        rest_exp += re_n
        rest_act += ra_n

        # Part-level scoring
        if len(parts) == 1:
            split = {parts[0]: rd}
        else:
            up, lo = split_parts(rd)
            split = {parts[0]: up, parts[-1]: lo}
            for mid in parts[1:-1]:
                split[mid] = []
        for pos, part in enumerate(parts):
            pick = None if len(parts) == 1 else ('top' if pos == 0 else 'bottom')
            p_exp = truth_tokens(truth, [part], pick)
            _, p_pairs = align_notes(p_exp, split[part])
            psc = tally_pairs(p_exp, split[part], p_pairs)
            for k, v in psc.items():
                if isinstance(v, int):
                    part_sum[k] += v

    exp_meter = norm_meter(truth.get('meter'))
    act_meter = norm_meter(out['meters'][0]) if out['meters'] else None
    meter_status = None if exp_meter is None else (act_meter == exp_meter)

    return {
        'id': case['id'],
        'kind': case.get('kind', 'clean'),
        'found_pages': out['found_pages'],
        'expected_pages': out['expected_pages'],
        'staff': dict(staff_sum),
        'parts': dict(part_sum),
        'rests': {'matched': rest_matched, 'expected': rest_exp, 'actual': rest_act},
        'meter_expected': exp_meter,
        'meter_actual': act_meter,
        'meter_ok': meter_status,
        'len_conf': len_conf,
        'pitch_err': pitch_err,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Evaluate scoreread with honest F1, rest, onset, and meter metrics.')
    parser.add_argument('--manifest', help='JSON manifest with cases and truth_dir (e.g., out/eval/clean_dev.json)')
    parser.add_argument('--kit', help='Path to SCOREREAD_KIT folder (uses cases.json and truth/)')
    parser.add_argument('--results', required=True, help='Folder holding reader MusicXML outputs')
    parser.add_argument('--tool', default='', help='Subfolder inside --results (for --kit mode, e.g., own)')
    parser.add_argument('--kind', default=None, help='Filter cases by kind (e.g., printed)')
    parser.add_argument('--json-out', default=None, help='Optional path to write full JSON summary')
    parser.add_argument('--top', type=int, default=15, help='Number of worst cases to list')
    args = parser.parse_args()

    if args.manifest:
        mpath = Path(args.manifest)
        data = json.loads(mpath.read_text(encoding='utf-8'))
        cases = data['cases']
        truth_dir = Path(data['truth_dir'])
        res_dir = Path(args.results)
    elif args.kit:
        kdir = Path(args.kit)
        cases = json.loads((kdir / 'cases.json').read_text(encoding='utf-8'))['cases']
        truth_dir = kdir / 'truth'
        res_dir = Path(args.results) / args.tool if args.tool else Path(args.results)
    else:
        parser.error('Pass either --manifest or --kit.')

    if args.kind:
        cases = [c for c in cases if c.get('kind') == args.kind]

    results = []
    tot_parts = Counter()
    tot_staff = Counter()
    tot_rests = Counter()
    tot_len = Counter()
    tot_pitch = Counter()
    meter_ok = meter_total = 0
    f1_99 = f1_999 = rec_99 = 0

    for case in cases:
        tpath = truth_dir / f"{case['id']}.json"
        if not tpath.exists():
            print(f"MISSING truth: {tpath}", file=sys.stderr)
            continue
        truth = json.loads(tpath.read_text(encoding='utf-8'))
        r = score_case(res_dir, case, truth)
        results.append(r)
        tot_parts.update(r['parts'])
        tot_staff.update(r['staff'])
        tot_rests.update(r['rests'])
        tot_len.update(r['len_conf'])
        tot_pitch.update(r['pitch_err'])
        if r['meter_ok'] is not None:
            meter_total += 1
            meter_ok += int(r['meter_ok'])
        _, prec_p, f1_p = prf(r['parts']['right'], r['parts']['expected'], r['parts']['read'])
        rec_p = r['parts']['right'] / r['parts']['expected'] if r['parts']['expected'] else 1.0
        if rec_p >= 0.99:
            rec_99 += 1
        if f1_p >= 0.99:
            f1_99 += 1
        if f1_p >= 0.999:
            f1_999 += 1

    pp, pr, pf1 = prf(tot_parts['right'], tot_parts['expected'], tot_parts['read'])
    sp, sr, sf1 = prf(tot_staff['right'], tot_staff['expected'], tot_staff['read'])
    rp, rr, rf1 = prf(tot_rests['matched'], tot_rests['expected'], tot_rests['actual'])
    onset_rate = tot_staff['onset_exact'] / max(1, tot_staff['right'])
    dt_rate = tot_staff['dt_ok'] / max(1, tot_staff['dt_total'])
    extra_pct = tot_parts['extra'] / max(1, tot_parts['expected'])

    print(f"=== HONEST EVALUATION ({len(results)} scores) ===")
    print(f"Parts level : F1={pf1:6.2%} | Prec={pp:6.2%} | Rec={pr:6.2%} | Right={tot_parts['right']}/{tot_parts['expected']} | Read={tot_parts['read']} | Extra={tot_parts['extra']} ({extra_pct:.2%}) | Missed={tot_parts['missed']}")
    print(f"Staff level : F1={sf1:6.2%} | Prec={sp:6.2%} | Rec={sr:6.2%} | Right={tot_staff['right']}/{tot_staff['expected']} | Read={tot_staff['read']} | Extra={tot_staff['extra']} | Missed={tot_staff['missed']}")
    print(f"Rests       : F1={rf1:6.2%} | Prec={rp:6.2%} | Rec={rr:6.2%} | Matched={tot_rests['matched']}/{tot_rests['expected']} (emitted {tot_rests['actual']})")
    print(f"Onsets      : exact={onset_rate:6.2%} ({tot_staff['onset_exact']}/{tot_staff['right']}) | dt={dt_rate:6.2%} ({tot_staff['dt_ok']}/{tot_staff['dt_total']})")
    print(f"Meters      : {meter_ok}/{meter_total} ({(meter_ok / meter_total if meter_total else 0.0):.1%})")
    print(f"Scores      : >=99% F1: {f1_99}/{len(results)} | >=99.9% F1: {f1_999}/{len(results)} | (>=99% recall-only: {rec_99}/{len(results)})")
    print(f"\nStaff error breakdown: extra={tot_staff['extra']} missed={tot_staff['missed']} len_only={tot_staff['len_only']} pitch_only={tot_staff['pitch_only']} both={tot_staff['both_wrong']}")
    print(f"Pitch errors : {dict(tot_pitch)}")
    print(f"Top length confusions: {tot_len.most_common(12)}")

    def loss(item: dict) -> int:
        p = item['parts']
        return (p['expected'] - p['right']) + p['extra']

    print(f"\nWorst {min(args.top, len(results))} scores by total note error (wrong + missed + extra):")
    for r in sorted(results, key=loss, reverse=True)[:args.top]:
        p = r['parts']
        prec, rec, f1 = prf(p['right'], p['expected'], p['read'])
        print(f"  {r['id']:40s} F1={f1:6.2%} P={prec:6.2%} R={rec:6.2%} | ok={p['right']:4d}/{p['expected']:4d} miss={p['missed']:3d} ext={p['extra']:3d} p={p['pitch_only']:2d} l={p['len_only']:2d} b={p['both_wrong']:2d}")

    if args.json_out:
        summary = {
            'scores': len(results),
            'parts': {'f1': pf1, 'precision': pp, 'recall': pr, **dict(tot_parts)},
            'staff': {'f1': sf1, 'precision': sp, 'recall': sr, **dict(tot_staff)},
            'rests': {'f1': rf1, 'precision': rp, 'recall': rr, **dict(tot_rests)},
            'onsets': {'exact': onset_rate, 'dt': dt_rate},
            'meters': {'ok': meter_ok, 'total': meter_total},
            'at_99_f1': f1_99,
            'at_999_f1': f1_999,
            'at_99_recall': rec_99,
            'pitch_errors': dict(tot_pitch),
            'length_confusions': dict(tot_len),
            'cases': [{k: (dict(v) if isinstance(v, Counter) else v) for k, v in r.items()} for r in results],
        }
        Path(args.json_out).write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    return 0


if __name__ == '__main__':
    sys.exit(main())

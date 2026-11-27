#!/usr/bin/env python3
"""Diagnostic tool for Clean Dev error analysis (NEVER run on clean_holdout.json).

Inspects MusicXML + .notes.json + truth JSONs for a Clean Dev run and classifies every
remaining error (extra phantom note, missed note, length confusion, pitch error, rest error)
with its visual features (hollow/filled, hole ratio, stem count, position, ledger count,
proximity to rests/dynamics/barlines/words) so engineering effort targets the highest-F1-impact
root causes first.

Usage:
  python3 bench/inspect_errors.py --manifest out/eval/clean_dev.json --results out/eval/baseline_dev
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench.eval_f1 import (
    align_notes,
    match_staves,
    read_case_outputs,
    reader_tokens,
    split_by_clef,
    truth_rests,
    truth_tokens,
)


def main() -> int:
    parser = argparse.ArgumentParser(description='Deep error taxonomy for Clean Dev.')
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--results', required=True)
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding='utf-8'))
    if 'holdout' in Path(args.manifest).name.lower():
        sys.exit('REFUSED: never run error inspection on the locked holdout split.')
    truth_dir = Path(manifest['truth_dir'])
    res_dir = Path(args.results)

    causes = Counter()
    extra_len = Counter()
    extra_hollow = Counter()
    missed_len = Counter()
    len_conf = Counter()
    pitch_off = Counter()
    rest_near_extra = 0
    total_extra = 0
    scores_with_large_miss = []

    for case in manifest['cases']:
        truth = json.loads((truth_dir / f"{case['id']}.json").read_text(encoding='utf-8'))
        out = read_case_outputs(res_dir, case)
        staves = split_by_clef(out['notes'], len(case['layout']))
        actual = [reader_tokens(s) for s in staves]
        expected = [truth_tokens(truth, parts) for parts in case['layout']]
        chosen = match_staves(expected, actual)

        case_miss = case_extra = case_exp = 0
        for row, (parts, exp_tok) in enumerate(zip(case['layout'], expected)):
            idx = chosen[row]
            rd = actual[idx] if idx is not None else []
            _, pairs = align_notes(exp_tok, rd)
            exp_r = truth_rests(truth, parts)
            rest_onsets = [r[0] for r in exp_r]
            case_exp += len(exp_tok)

            for r, k in pairs:
                if r is None:
                    total_extra += 1
                    case_extra += 1
                    extra_len[str(rd[k][1])] += 1
                    # Check if an expected rest stands near this onset
                    if any(abs(rd[k][0] - ro) <= Fraction(2) for ro in rest_onsets):
                        rest_near_extra += 1
                elif k is None:
                    case_miss += 1
                    missed_len[str(exp_tok[r][1])] += 1
                else:
                    sp = exp_tok[r][2] == rd[k][2]
                    sl = exp_tok[r][1] == rd[k][1]
                    if sp and sl:
                        continue
                    if not sp and sl:
                        dp = rd[k][2] - exp_tok[r][2]
                        pitch_off[dp] += 1
                        if abs(dp) == 1:
                            causes['pitch_semitone (accidental/key)'] += 1
                        elif abs(dp) == 12:
                            causes['pitch_octave (clef/G8vb)'] += 1
                        elif abs(dp) <= 4:
                            causes['pitch_1_2_steps (ledger/head_y)'] += 1
                        else:
                            causes['pitch_large (clef/staff_shift)'] += 1
                    elif sp and not sl:
                        key = f'{exp_tok[r][1]}->{rd[k][1]}'
                        len_conf[key] += 1
                        e_ln, a_ln = exp_tok[r][1], rd[k][1]
                        if (e_ln == Fraction(2) and a_ln == Fraction(1)) or (e_ln == Fraction(1) and a_ln == Fraction(2)):
                            causes['len_half_vs_quarter (hollow/filled)'] += 1
                        elif (e_ln == Fraction(4) and a_ln == Fraction(2)) or (e_ln == Fraction(2) and a_ln == Fraction(4)):
                            causes['len_whole_vs_half (stem_attachment)'] += 1
                        elif (e_ln == Fraction(1, 2) and a_ln == Fraction(1)) or (e_ln == Fraction(1) and a_ln == Fraction(1, 2)):
                            causes['len_eighth_vs_quarter (flag/beam/slur)'] += 1
                        elif e_ln in (Fraction(3), Fraction(3, 2), Fraction(3, 4)) or a_ln in (Fraction(3), Fraction(3, 2), Fraction(3, 4)):
                            causes['len_dot_or_tie (dot/tie_missed_or_false)'] += 1
                        elif e_ln == Fraction(1, 4) or a_ln == Fraction(1, 4):
                            causes['len_sixteenth (second_beam/flag)'] += 1
                        elif e_ln.denominator == 3 or a_ln.denominator == 3:
                            causes['len_triplet'] += 1
                        else:
                            causes['len_other (tie/breve/bar)'] += 1
                    else:
                        causes['both_pitch_and_len'] += 1

        if case_miss >= 15 or case_extra >= 15:
            scores_with_large_miss.append((case['id'], case_exp, case_miss, case_extra, len(actual), len(expected)))

    print('=== CLEAN DEV DEEP ERROR TAXONOMY (STAFF LEVEL) ===')
    print(f'Total extra phantom notes : {total_extra} (near truth rest onset: {rest_near_extra})')
    print(f'Extra notes by duration   : {extra_len.most_common(10)}')
    print(f'Missed notes by duration  : {missed_len.most_common(10)}')
    print('\nPitch + length root causes:')
    for k, v in causes.most_common():
        print(f'  {k:44s}: {v:4d}')
    print(f'\nTop length confusions: {len_conf.most_common(15)}')
    print(f'Top pitch offsets (semitones): {pitch_off.most_common(12)}')
    print('\nScores with >=15 missed or >=15 extra notes (id, exp, miss, extra, read_staves, exp_staves):')
    for row in sorted(scores_with_large_miss, key=lambda x: -(x[2] + x[3])):
        print(f'  {row[0]:42s} exp={row[1]:4d} miss={row[2]:3d} ext={row[3]:3d} staves={row[4]}/{row[5]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())

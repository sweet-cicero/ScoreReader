#!/usr/bin/env python3
"""Scores the experiment's methods with the kit's score.py and prints one line for each method.

usage: report.py [method ...]      (every folder in results/ when none is named)
"""
import json
import os
import sys

EXP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(EXP))
import score  # noqa: E402


def main():
    results = os.path.join(EXP, 'results')
    methods = sys.argv[1:] or sorted(name for name in os.listdir(results) if os.path.isdir(os.path.join(results, name)))
    with open(os.path.join(EXP, 'cases.json')) as file:
        case = json.load(file)['cases'][0]
    with open(os.path.join(score.KIT, 'truth', case['id'] + '.json')) as file:
        truth = json.load(file)
    print(f"{'method':<34} {'right':>6} {'pitch':>6} {'length':>6} {'missed':>6} {'extra':>6}   staff  sop  alto  read")
    for method in methods:
        scored, lines = score.score_case(results, method, case, truth)
        with open(os.path.join(results, method, case['id'] + '.diff.txt'), 'w') as file:
            file.write('\n'.join(lines) + '\n')
        total = {}
        for counts in scored['parts'].values():
            score.add(total, counts)
        notes = total['notes']
        staff = scored['staff']
        parts = scored['parts']
        print(f"{method:<34} {100 * total['right'] / notes:5.1f}% {100 * total['pitch'] / notes:5.1f}% "
              f"{100 * total['length'] / notes:5.1f}% {100 * total['missed'] / notes:5.1f}% {100 * total['extra'] / notes:5.1f}%  "
              f"{100 * staff['right'] / staff['notes']:5.1f}% "
              f"{100 * parts['soprano']['right'] / parts['soprano']['notes']:4.0f}% "
              f"{100 * parts['alto']['right'] / parts['alto']['notes']:4.0f}%  {staff['read']} notes, {scored['reader_staves']} staves")


if __name__ == '__main__':
    main()

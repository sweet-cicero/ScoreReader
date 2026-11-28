#!/usr/bin/env python3
"""Extracts labelled 3-channel (3, 32, 32) symbol crops strictly from Clean Dev pages.

Refuses to run on any manifest containing 'holdout' or non-dev splits to enforce zero
holdout leakage. Avoids tie-join duration poisoning by labelling noteheads only from
exact untied (pitch, length) matches against Clean Dev truth.

Extracts real Clean Dev crops for:
  - head_filled, head_hollow, head_whole, head_breve (verified against truth)
  - rest_quarter, rest_half, rest_whole, rest_eighth (verified against truth rests)
  - acc_sharp, acc_flat, acc_natural (verified in-bar note_signs and truth key signatures)
  - clef_G, clef_F (verified staff starts matching truth clefs)
  - fermata (detected fermatas on Clean Dev pages)
  - noise (hard negatives: unmatched phantom notes on clean 1-to-1 scores, non-head thick
    marks outside all head/orphan/rest/accidental/fermata boxes on high-recall scores,
    barline blobs, time-signature digits, lyric letters, beam/flag tips, and down-stem necks)

Usage:
  $PY tools/extract_dev_crops.py --manifest out/eval/clean_dev.json \
      --results /tmp/scorereader_swarm/step3_dev --out /tmp/scorereader_swarm/dev_crops_v2.npz
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import json
import sys
import time
from collections import Counter
from fractions import Fraction
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bench.eval_f1 import (
    align_notes,
    align_rests,
    match_staves,
    read_case_outputs,
    reader_tokens,
    split_by_clef,
    truth_rests,
    truth_tokens,
)
from scorereader.classify import CLASS_TO_ID, CLASSES, PATCH_SIZE, extract_patch, page_levels
from scorereader.fermatas import fermatas
from scorereader.layers import read_layers
from scorereader.meter import mid_signs
from scorereader.music import key_alters
from scorereader.rests import block_rests, eighth_rests, neural_rest_candidates, quarter_rests
from scorereader.signs import note_signs
from scorereader.starts import read_starts
from scorereader.symbols import bar_lines, read_symbols
from scorereader.words import word_bands

# Exclude multi-hymn booklet or duplicate-copy scores from negative mining
# so real notes on extra pages are never mislabelled as noise.
SKIP_NEGATIVE_IDS = {
    'wedding-service',
    'transfiguration-koinonikon-serbian',
    'memorial-troparia--s2',
    'communion-lords-prayer',
}

KEY_TO_FIFTHS = {
    'C': 0, 'Am': 0,
    'G': 1, 'Em': 1,
    'D': 2, 'Bm': 2,
    'A': 3, 'F#m': 3,
    'E': 4, 'C#m': 4,
    'B': 5, 'G#m': 5,
    'F#': 6, 'D#m': 6,
    'F': -1, 'Dm': -1,
    'Bb': -2, 'Gm': -2,
    'Eb': -3, 'Cm': -3,
    'Ab': -4, 'Fm': -4,
    'Db': -5, 'Bbm': -5,
    'Gb': -6, 'Ebm': -6,
}

STEP_TO_INDEX = {'C': 0, 'D': 1, 'E': 2, 'F': 3, 'G': 4, 'A': 5, 'B': 6}


def _box_overlaps(cx: float, cy: float, boxes: list[tuple[float, float, float, float]], pad: float) -> bool:
    for x0, y0, x1, y1 in boxes:
        if x0 - pad <= cx <= x1 + pad and y0 - pad <= cy <= y1 + pad:
            return True
    return False


def _rects_overlap(a: tuple[float, float, float, float], b: tuple[float, float, float, float], pad_x: float, pad_y: float) -> bool:
    return a[0] - pad_x <= b[2] and b[0] <= a[2] + pad_x and a[1] - pad_y <= b[3] and b[1] <= a[3] + pad_y


def _rest_cls_for_truth_len(ln: Fraction) -> str | None:
    if ln in (Fraction(1, 2), Fraction(3, 4)):
        return 'rest_eighth'
    if ln in (Fraction(1), Fraction(3, 2)):
        return 'rest_quarter'
    if ln in (Fraction(2), Fraction(3)):
        return 'rest_half'
    if ln >= Fraction(4):
        return 'rest_whole'
    return None


def _extract_one_case(task: tuple[dict, str, str, int, int]) -> tuple[list[np.ndarray], list[int], list[str], Counter]:
    """Extracts verified symbol crops for one Clean Dev case."""
    case, truth_dir_s, res_dir_s, max_noise_per_page, seed = task
    truth_dir = Path(truth_dir_s)
    res_dir = Path(res_dir_s)
    rng = np.random.default_rng(seed)

    patches: list[np.ndarray] = []
    labels: list[int] = []
    groups: list[str] = []
    counts: Counter = Counter()

    def add_crop(grey: np.ndarray, bare: np.ndarray, staff: dict, cx: float, cy: float,
                 levels: tuple[float, float], cls_name: str, base_id: str) -> None:
        patch = extract_patch(grey, bare, staff['rows'], staff['space'], cx, cy,
                              size=PATCH_SIZE, levels=levels)
        patches.append((patch * 255.0).round().astype(np.uint8))
        labels.append(CLASS_TO_ID[cls_name])
        groups.append(base_id)
        counts[cls_name] += 1

    cid = case['id']
    base_id = case.get('base_id', cid.split('--')[0])
    tpath = truth_dir / f'{cid}.json'
    if not tpath.exists():
        return patches, labels, groups, counts
    truth = json.loads(tpath.read_text(encoding='utf-8'))
    out = read_case_outputs(res_dir, case)
    layout = case['layout']
    if layout == [['melody', 'ison']] and len(out['notes']) == 2:
        layout = [['melody'], ['ison']]
    staves_out = split_by_clef(out['notes'], len(layout))
    actual = [reader_tokens(s) for s in staves_out]
    expected = [truth_tokens(truth, parts) for parts in layout]
    chosen = match_staves(expected, actual)

    # Build exact (midi, length) match counters and unmatched extra counters per part index.
    exact_matched: dict[int, Counter] = {}
    extra_keys: dict[int, Counter] = {}
    part_clefs_truth: dict[int, str] = {}
    part_rest_budget: dict[int, Counter] = {}
    case_missed = 0
    case_extra = 0
    case_rest_missed = 0

    for row, (parts, exp_tok) in enumerate(zip(layout, expected)):
        idx = chosen[row]
        if idx is None:
            case_missed += len(exp_tok)
            continue
        rd = actual[idx]
        _, pairs = align_notes(exp_tok, rd)
        mk = exact_matched.setdefault(idx, Counter())
        ek = extra_keys.setdefault(idx, Counter())
        for r, k in pairs:
            if r is None and k is not None:
                ek[(rd[k][2], rd[k][1])] += 1
                case_extra += 1
            elif r is not None and k is None:
                case_missed += 1
            elif r is not None and k is not None:
                if exp_tok[r][2] == rd[k][2] and exp_tok[r][1] == rd[k][1]:
                    mk[(rd[k][2], rd[k][1])] += 1

        # Record truth clef for this part index.
        t_clefs = truth.get('clefs') or {}
        part_clef_vals = {t_clefs.get(p) for p in parts if t_clefs.get(p)}
        if len(part_clef_vals) == 1:
            cname = next(iter(part_clef_vals))
            if cname == 'treble':
                part_clefs_truth[idx] = 'G'
            elif cname == 'bass':
                part_clefs_truth[idx] = 'F'

        # Compute truth rest budget and missed-rest count for this part index.
        exp_r = truth_rests(truth, parts)
        act_r_raw = out['rests'][idx] if idx < len(out['rests']) else []
        seen_r = set()
        act_r = []
        for r in act_r_raw:
            key = (r['on'], r['len'])
            if key not in seen_r and r['len'] > 0:
                seen_r.add(key)
                act_r.append(key)
        act_r.sort()
        rm, re_n, _ = align_rests(exp_r, act_r)
        case_rest_missed += max(0, re_n - rm)

        rb = part_rest_budget.setdefault(idx, Counter())
        for _, ln in exp_r:
            rcls = _rest_cls_for_truth_len(ln)
            if rcls is not None:
                rb[rcls] += 1
            # In 3/4 or 3/2 meter a hanging whole rest encodes a full 3-beat bar rest.
            if ln == Fraction(3) and truth.get('meter') in ('3/4', '3/2'):
                rb['rest_whole'] += 1

    truth_fifths = KEY_TO_FIFTHS.get(str(truth.get('key', '')))
    case_clef_taken: Counter = Counter()
    case_keysig_taken: Counter = Counter()
    case_fermata_taken = 0
    high_recall_case = (cid not in SKIP_NEGATIVE_IDS) and (case_missed <= 2) and (case_rest_missed == 0)

    for seq_idx in range(1, len(case['pages']) + 1):
        stem = f'{cid}-p{seq_idx}'
        clean_p = res_dir / f'{stem}.clean.png'
        lay_p = res_dir / f'{stem}.layout.json'
        notes_p = res_dir / f'{stem}.notes.json'
        if not (clean_p.exists() and lay_p.exists() and notes_p.exists()):
            continue
        grey = cv2.imread(str(clean_p), cv2.IMREAD_GRAYSCALE)
        if grey is None:
            continue
        layout_json = json.loads(lay_p.read_text(encoding='utf-8'))
        notes_json = json.loads(notes_p.read_text(encoding='utf-8'))
        places = layout_json.get('clean_page') or []
        if not places:
            continue

        layers = read_layers(grey, places)
        layers['words'] = word_bands(layers)
        bare = layers['bare']
        staves_info = layers['staves']
        space = float(layers['space'])
        levels = page_levels(grey)

        syms = read_symbols(layers)
        begin = read_starts(layers)
        ends = begin['ends']
        bars = bar_lines(layers, syms['heads'])
        times = mid_signs(layers, ends, bars)
        holds = fermatas(layers)

        # Build per-staff exclusion boxes covering all real symbols and uncertain orphans.
        occupied: dict[int, list[tuple[float, float, float, float]]] = {i: [] for i in range(len(staves_info))}
        staff_head_boxes: dict[int, list[tuple[float, float, float, float]]] = {i: [] for i in range(len(staves_info))}
        staff_stem_spans: dict[int, list[tuple[float, float, float]]] = {i: [] for i in range(len(staves_info))}

        for h in syms['heads'] + syms['orphans']:
            si = h.get('staff')
            if si is not None and 0 <= si < len(staves_info):
                box = (float(h['x0']), float(h['y0']), float(h['x1']), float(h['y1']))
                occupied[si].append(box)
                staff_head_boxes[si].append(box)
                for st_item in h.get('stems', []):
                    y_lo = min(float(h['cy']), float(st_item['end']))
                    y_hi = max(float(h['cy']), float(st_item['end']))
                    staff_stem_spans[si].append((float(st_item['x']), y_lo, y_hi))

        for sg in syms['signs']:
            si = sg.get('staff')
            if si is not None and 0 <= si < len(staves_info):
                occupied[si].append((float(sg['x0']), float(sg['y0']), float(sg['x1']), float(sg['y1'])))

        # 1. Verified Clean Dev rests (quarter, half, whole, eighth, plus verified neural slim rests).
        q_rests = quarter_rests(layers, ends)
        b_rests = block_rests(layers, ends)
        e_rests = eighth_rests(layers, ends, syms['heads'], bars)
        n_rests = neural_rest_candidates(layers, ends, syms['heads'], bars, q_rests + b_rests + e_rests)

        rest_boxes_by_staff: dict[int, list[tuple[float, float, float, float]]] = {i: [] for i in range(len(staves_info))}
        for r in q_rests + b_rests + e_rests + n_rests:
            si = r['staff']
            if 0 <= si < len(staves_info):
                rbox = (float(r['x0']), float(r['top']), float(r['x1']), float(r['bottom']))
                occupied[si].append(rbox)
                rest_boxes_by_staff[si].append(rbox)

        emitted_rest_pts: set[tuple[int, int]] = set()

        def _take_rest(si: int, r: dict, rcls: str) -> None:
            part_idx = staves_info[si]['number']
            if part_rest_budget.get(part_idx, Counter())[rcls] <= 0:
                return
            rx_bin = int(round(float(r['x']) / max(1.0, 0.7 * space)))
            if (si, rx_bin) in emitted_rest_pts:
                return
            part_rest_budget[part_idx][rcls] -= 1
            emitted_rest_pts.add((si, rx_bin))
            add_crop(grey, bare, staves_info[si], float(r['x']), 0.5 * (r['top'] + r['bottom']),
                     levels, rcls, base_id)

        for r in q_rests:
            _take_rest(r['staff'], r, 'rest_quarter')

        for r in b_rests:
            hangs = bool(r.get('hangs'))
            sits = bool(r.get('sits'))
            if hangs and not sits:
                rcls = 'rest_whole'
            elif sits and not hangs:
                rcls = 'rest_half'
            else:
                rcls = 'rest_whole' if r.get('length') == Fraction(4) else 'rest_half'
            _take_rest(r['staff'], r, rcls)

        for r in e_rests:
            si = r['staff']
            rcls = 'rest_16th' if r.get('kind') == '16th' else 'rest_eighth'
            if rcls != 'rest_eighth':
                continue
            rbox = (float(r['x0']), float(r['top']), float(r['x1']), float(r['bottom']))
            if any(_rects_overlap(rbox, hb, 0.25 * space, 0.25 * space) for hb in staff_head_boxes[si]):
                continue
            if any(rbox[0] - 0.30 * space <= sx <= rbox[2] + 0.30 * space and y_lo <= rbox[3] and rbox[1] <= y_hi
                   for sx, y_lo, y_hi in staff_stem_spans[si]):
                continue
            _take_rest(si, r, 'rest_eighth')

        # Verified neural slim/faded rests (strictly budgeted by Clean Dev truth rest counts).
        for r in n_rests:
            si = r['staff']
            rkind = r.get('kind')
            if rkind == 'quarter':
                rcls = 'rest_quarter'
            elif rkind == 'eighth':
                rcls = 'rest_eighth'
            elif rkind == 'block':
                hangs, sits = bool(r.get('hangs')), bool(r.get('sits'))
                if hangs and not sits:
                    rcls = 'rest_whole'
                elif sits and not hangs:
                    rcls = 'rest_half'
                else:
                    rcls = 'rest_whole' if r.get('length') == Fraction(4) else 'rest_half'
            else:
                continue
            rbox = (float(r['x0']), float(r['top']), float(r['x1']), float(r['bottom']))
            if any(_rects_overlap(rbox, hb, 0.25 * space, 0.25 * space) for hb in staff_head_boxes[si]):
                continue
            _take_rest(si, r, rcls)

        # 2. Verified Clean Dev fermatas.
        fermata_boxes: list[tuple[float, float, float, float]] = []
        for f in holds:
            fbox = (float(f['x0']), float(f['top']), float(f['x1']), float(f['bottom']))
            fermata_boxes.append(fbox)
            fy = 0.5 * (f['top'] + f['bottom'])
            best_si = min(range(len(staves_info)),
                          key=lambda i: abs(fy - staves_info[i]['rows'][2]))
            st = staves_info[best_si]
            occupied[best_si].append(fbox)
            if abs(fy - st['rows'][2]) <= 6.0 * st['space'] and case_fermata_taken < 20:
                case_fermata_taken += 1
                add_crop(grey, bare, st, float(f['x']), fy, levels, 'fermata', base_id)

        # 3. Verified Clean Dev clefs and key-signature accidentals.
        for si, st_info in enumerate(begin['starts']):
            staff = staves_info[si]
            part_idx = staff['number']
            want_clef = part_clefs_truth.get(part_idx)
            got_clef = st_info.get('clef')
            if got_clef in ('G', 'F') and got_clef == want_clef:
                x0, x1 = st_info.get('x0'), st_info.get('x1')
                if x0 is not None and x1 is not None and x1 > x0:
                    clef_cls = f'clef_{got_clef}'
                    if case_clef_taken[clef_cls] < 12:
                        case_clef_taken[clef_cls] += 1
                        add_crop(grey, bare, staff, 0.5 * (float(x0) + float(x1)),
                                 float(staff['rows'][2]), levels, clef_cls, base_id)

            if truth_fifths is not None and truth_fifths != 0 and st_info.get('key') == truth_fifths and float(st_info.get('miss', 1.0)) < 0.35:
                kind_key = 'sharp' if truth_fifths > 0 else 'flat'
                acc_cls = 'acc_sharp' if truth_fifths > 0 else 'acc_flat'
                chain_entry = (st_info.get('chains') or {}).get((got_clef, kind_key))
                if chain_entry and len(chain_entry[0]) == abs(truth_fifths):
                    for ks in chain_entry[0]:
                        if case_keysig_taken[acc_cls] >= 12:
                            break
                        if 'top' not in ks or 'bottom' not in ks or 'x0' not in ks or 'x1' not in ks:
                            continue
                        kx0, kx1 = float(ks['x0']), float(ks['x1'])
                        ktop, kbot = float(ks['top']), float(ks['bottom'])
                        if kx1 > kx0 and kbot > ktop:
                            case_keysig_taken[acc_cls] += 1
                            add_crop(grey, bare, staff, 0.5 * (kx0 + kx1), 0.5 * (ktop + kbot),
                                     levels, acc_cls, base_id)

        # 4. Matched Clean Dev noteheads (zero tie-join poisoning) and phantom extra notes.
        page_matched_notes: dict[int, list[dict]] = {i: [] for i in range(len(staves_info))}
        extra_noise_pts: dict[int, list[tuple[float, float]]] = {i: [] for i in range(len(staves_info))}

        for note in notes_json.get('notes', []):
            si = note.get('staff')
            if si is None or not (0 <= si < len(staves_info)):
                continue
            staff = staves_info[si]
            part_idx = staff['number']
            mark = note.get('mark') or {}
            cx = float(note['x'])
            cy = float(mark.get('y', staff['rows'][2]))
            mw = float(mark.get('wide', space))
            mh = float(mark.get('high', space))
            occupied[si].append((cx - 0.5 * mw, cy - 0.5 * mh, cx + 0.5 * mw, cy + 0.5 * mh))
            if mark.get('dot'):
                occupied[si].append((cx + 0.4 * space, cy - 0.5 * space, cx + 1.4 * space, cy + 0.5 * space))

            midi = int(note['midi'])
            nlen = Fraction(note['length']).limit_denominator(192)
            key = (midi, nlen)
            is_tied = bool(note.get('tie_start') or note.get('tie_stop'))

            if not is_tied and exact_matched.get(part_idx, Counter()).get(key, 0) > 0:
                exact_matched[part_idx][key] -= 1
                stems = mark.get('stems') or []
                cls_name = None
                if nlen < Fraction(2):
                    cls_name = 'head_filled'
                elif nlen in (Fraction(2), Fraction(3)):
                    cls_name = 'head_hollow'
                elif nlen in (Fraction(4), Fraction(6)) and not stems:
                    cls_name = 'head_whole'
                elif nlen >= Fraction(8) and not stems:
                    cls_name = 'head_breve'
                if cls_name is not None:
                    add_crop(grey, bare, staff, cx, cy, levels, cls_name, base_id)
                    page_matched_notes[si].append(note)
            elif (not is_tied) and (cid not in SKIP_NEGATIVE_IDS) and (case_missed <= 3) and extra_keys.get(part_idx, Counter()).get(key, 0) > 0:
                extra_keys[part_idx][key] -= 1
                if not _box_overlaps(cx, cy, rest_boxes_by_staff[si] + fermata_boxes, 0.35 * space):
                    extra_noise_pts[si].append((cx, cy))

        # 5. Verified Clean Dev in-bar accidentals (note_signs matched to altered exact notes).
        page_key_alters = key_alters(truth_fifths) if truth_fifths is not None else {}
        kind_to_alter = {'sharp': 1, 'flat': -1, 'natural': 0}
        for si in range(len(staves_info)):
            staff = staves_info[si]
            ns_list = note_signs(layers, si, syms['heads'], ends[si])
            for sg in ns_list:
                if 'top' not in sg or 'bottom' not in sg or 'x0' not in sg or 'x1' not in sg:
                    continue
                occupied[si].append((float(sg['x0']), float(sg['top']), float(sg['x1']), float(sg['bottom'])))
                sg_kind = sg.get('kind')
                if sg_kind not in kind_to_alter:
                    continue
                head_ref = sg.get('head')
                if not head_ref:
                    continue
                hx, hy = float(head_ref['cx']), float(head_ref['cy'])
                matched_n = next(
                    (n for n in page_matched_notes[si]
                     if abs(float(n['x']) - hx) <= 0.6 * space
                     and abs(float((n.get('mark') or {}).get('y', hy)) - hy) <= 0.6 * space),
                    None,
                )
                if matched_n is None:
                    continue
                step_idx = STEP_TO_INDEX.get(str(matched_n.get('step', '')).upper())
                if step_idx is None:
                    continue
                want_alter = kind_to_alter[sg_kind]
                note_alter = int(matched_n.get('alter', 0))
                key_alt = page_key_alters.get(step_idx, 0)
                if note_alter == want_alter and (note_alter != key_alt or sg_kind == 'natural'):
                    add_crop(grey, bare, staff, 0.5 * (float(sg['x0']) + float(sg['x1'])),
                             0.5 * (float(sg['top']) + float(sg['bottom'])),
                             levels, f'acc_{sg_kind}', base_id)

        # 6. Hard negatives ('noise'): phantom extra notes + verified non-head marks on Clean Dev pages.
        if cid in SKIP_NEGATIVE_IDS:
            continue

        noise_cands: list[tuple[int, float, float, int]] = []

        for si, pts in extra_noise_pts.items():
            for nx, ny in pts:
                noise_cands.append((si, nx, ny, 0))

        for si, staff in enumerate(staves_info):
            sp = float(staff['space'])
            rows = staff['rows']
            occ = occupied[si]

            for tsign in times.get(si, []):
                tx = 0.5 * (float(tsign['x0']) + float(tsign['x1']))
                for ty in (0.5 * (rows[0] + rows[2]), 0.5 * (rows[2] + rows[4])):
                    if not _box_overlaps(tx, ty, occ, 0.45 * sp):
                        noise_cands.append((si, tx, ty, 1))

            for n in page_matched_notes[si]:
                mk = n.get('mark') or {}
                st_info = mk.get('stem')
                if not st_info:
                    continue
                sx = float(st_info['x'])
                send = float(st_info['end'])
                ny = float(mk.get('y', rows[2]))
                if send > ny + 1.5 * sp:
                    py = ny + 1.35 * sp
                    if not _box_overlaps(sx, py, occ, 0.70 * sp):
                        noise_cands.append((si, sx, py, 2))
                if int(st_info.get('tails', 0)) >= 1:
                    if not _box_overlaps(sx, send, occ, 0.70 * sp):
                        noise_cands.append((si, sx, send, 2))

            for bx in bars.get(si, []):
                if bx > ends[si] + 1.0 * sp and bx < staff['x1'] - 0.5 * sp:
                    by = float(rows[2])
                    if not _box_overlaps(bx, by, occ, 0.75 * sp):
                        noise_cands.append((si, float(bx), by, 3))

        if high_recall_case:
            for mk in syms['marks']:
                mx, my = float(mk['cx']), float(mk['cy'])
                best_si = min(range(len(staves_info)),
                              key=lambda i: abs(my - staves_info[i]['rows'][2]))
                st = staves_info[best_si]
                sp = float(st['space'])
                if not (st['x0'] <= mx <= st['x1'] and mx > ends[best_si] + 0.6 * sp):
                    continue
                if not (st['rows'][0] - 2.6 * sp <= my <= st['rows'][4] + 2.6 * sp):
                    continue
                if _box_overlaps(mx, my, occupied[best_si], 0.70 * sp):
                    continue
                noise_cands.append((best_si, mx, my, 1))

            tc, _, tstats, tcent = cv2.connectedComponentsWithStats(layers['thick'].astype(np.uint8), connectivity=8)
            for k in range(1, tc):
                area = int(tstats[k, cv2.CC_STAT_AREA])
                if area < int(0.10 * space * space):
                    continue
                mx, my = float(tcent[k][0]), float(tcent[k][1])
                best_si = min(range(len(staves_info)),
                              key=lambda i: abs(my - staves_info[i]['rows'][2]))
                st = staves_info[best_si]
                sp = float(st['space'])
                if not (st['x0'] <= mx <= st['x1'] and mx > ends[best_si] + 0.6 * sp):
                    continue
                if not (st['rows'][0] - 2.6 * sp <= my <= st['rows'][4] + 2.6 * sp):
                    continue
                if _box_overlaps(mx, my, occupied[best_si], 0.75 * sp):
                    continue
                noise_cands.append((best_si, mx, my, 2))

        for wb in layers.get('words', []):
            wy = 0.5 * (float(wb['top']) + float(wb['bottom']))
            best_si = min(range(len(staves_info)),
                          key=lambda i: abs(wy - staves_info[i]['rows'][2]))
            st = staves_info[best_si]
            sp = float(st['space'])
            if abs(wy - st['rows'][2]) > 4.2 * sp:
                continue
            x0_b = max(int(ends[best_si] + sp), int(wb['x0']))
            x1_b = min(bare.shape[1] - 1, int(wb['x1']))
            y0_b = max(0, int(wb['top']))
            y1_b = min(bare.shape[0] - 1, int(wb['bottom']))
            if x1_b <= x0_b + 5 or y1_b <= y0_b + 3:
                continue
            wc, _, wstats, wcent = cv2.connectedComponentsWithStats(
                np.ascontiguousarray(bare[y0_b:y1_b, x0_b:x1_b].astype(np.uint8)), connectivity=8)
            w_picks = []
            for k in range(1, wc):
                if int(wstats[k, cv2.CC_STAT_AREA]) >= int(0.08 * sp * sp):
                    w_picks.append((x0_b + float(wcent[k][0]), y0_b + float(wcent[k][1])))
            if len(w_picks) > 6:
                idxs = rng.choice(len(w_picks), size=6, replace=False)
                w_picks = [w_picks[i] for i in idxs]
            for wx, wy_c in w_picks:
                if not _box_overlaps(wx, wy_c, occupied[best_si], 0.70 * sp):
                    noise_cands.append((best_si, wx, wy_c, 3))

        rng.shuffle(noise_cands)
        noise_cands.sort(key=lambda item: item[3])
        kept_noise: list[tuple[int, float, float]] = []
        for si, nx, ny, _ in noise_cands:
            if len(kept_noise) >= max_noise_per_page:
                break
            sp = float(staves_info[si]['space'])
            if any(ksi == si and abs(kx - nx) < 0.85 * sp and abs(ky - ny) < 0.85 * sp for ksi, kx, ky in kept_noise):
                continue
            kept_noise.append((si, nx, ny))
            add_crop(grey, bare, staves_info[si], nx, ny, levels, 'noise', base_id)

    return patches, labels, groups, counts


def main() -> int:
    parser = argparse.ArgumentParser(description='Extract zero-leakage Clean Dev symbol crops.')
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--results', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--max-noise-per-page', type=int, default=65)
    parser.add_argument('--workers', type=int, default=6)
    args = parser.parse_args()

    mpath = Path(args.manifest)
    if 'holdout' in mpath.name.lower() or 'clean_all' in mpath.name.lower():
        sys.exit('REFUSED: never extract training crops from holdout or combined manifest.')

    manifest = json.loads(mpath.read_text(encoding='utf-8'))
    if manifest.get('split') != 'clean_dev':
        sys.exit(f"REFUSED: expected manifest split 'clean_dev', got {manifest.get('split')!r}.")

    t0 = time.time()
    tasks = [
        (case, str(manifest['truth_dir']), str(args.results), args.max_noise_per_page, 2026 + i)
        for i, case in enumerate(manifest['cases'])
    ]

    patches: list[np.ndarray] = []
    labels: list[int] = []
    groups: list[str] = []
    counts: Counter = Counter()

    if args.workers > 1:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            for done_i, (p, l, g, c) in enumerate(pool.map(_extract_one_case, tasks), 1):
                patches.extend(p)
                labels.extend(l)
                groups.extend(g)
                counts.update(c)
                if done_i % 10 == 0 or done_i == len(tasks):
                    print(f'  processed {done_i}/{len(tasks)} Clean Dev cases ({len(labels)} crops, {time.time() - t0:.1f}s)', flush=True)
    else:
        for done_i, task in enumerate(tasks, 1):
            p, l, g, c = _extract_one_case(task)
            patches.extend(p)
            labels.extend(l)
            groups.extend(g)
            counts.update(c)
            if done_i % 10 == 0 or done_i == len(tasks):
                print(f'  processed {done_i}/{len(tasks)} Clean Dev cases ({len(labels)} crops, {time.time() - t0:.1f}s)', flush=True)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    X = np.stack(patches, axis=0) if patches else np.zeros((0, 3, PATCH_SIZE, PATCH_SIZE), np.uint8)
    Y = np.array(labels, dtype=np.int16)
    G = np.array(groups)
    np.savez_compressed(out_path, X=X, Y=Y, G=G, classes=np.array(CLASSES))
    print(f'Extracted {len(Y)} Clean Dev crops from {len(set(groups))} base hymns in {time.time() - t0:.1f}s -> {out_path}')
    for cls_name, cnt in counts.most_common():
        print(f'  {cls_name:16s}: {cnt:6d}')
    return 0


if __name__ == '__main__':
    sys.exit(main())

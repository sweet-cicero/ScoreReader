#!/usr/bin/env python3
"""Trains local offline StemNet, TimeNet, and AccNet with PyTorch CPU and exports compact NumPy weights.

Zero cloud dependency, zero holdout leakage:
1. TimeNet v3 (timenet_v3.npz, ~103 KB):
   Classifies (1, 24, 24) time-signature glyph crops into 10 classes:
     '2', '3', '4', '6', '8', '9', '12', 'C', 'cut', 'other'
   Combines staff-row-only bridged procedural engraved digits, 5-font Verovio SMuFL time crops
   (including Petaluma), and Clean Dev time crops with 5-fold grouped CV verification.

2. StemNet v3 (stemnet_v3.npz, ~103 KB):
   Classifies canonical stem-tip patches (3, 32, 32) spanning 4.5 x 4.5 staff spaces into 3 classes:
     0: 0 tails | 1: 1 tail | 2: 2 tails
   Combines procedural stems, 5-font Verovio stem crops (2,407 real 16th-note tail_2 crops!),
   and exact untied Clean Dev stems with 5-fold grouped CV calibration.

3. AccNet v1 (accnet_v1.npz, <=100 KB):
   Dedicated 4-class left-of-head accidental classifier ('none', 'sharp', 'flat', 'natural')
   on (3, 32, 32) 3.5-space patches trained on 4,069 5-font Verovio SMuFL accidentals, verified
   Clean Dev accidentals, procedural synthetic accidentals, and thousands of real hard left-of-head
   negatives (barlines, stems, neighbor heads, rests, beams, slurs, lyrics).

Usage:
  $PY tools/train_stem_and_time.py --manifest out/eval/clean_dev.json \
      --results /tmp/scorereader_swarm/step45_v2_final \
      --dev-crops /tmp/scorereader_swarm/dev_crops_v2.npz \
      --verovio-time /tmp/scorereader_swarm/verovio_time_crops.npz \
      --verovio-stem /tmp/scorereader_swarm/verovio_stem_crops.npz \
      --verovio-sym /tmp/scorereader_swarm/verovio_synth_crops.npz \
      --time-out /tmp/scorereader_swarm/timenet_v3.npz \
      --stem-out /tmp/scorereader_swarm/stemnet_v3.npz \
      --acc-out /tmp/scorereader_swarm/accnet_v1.npz --threads 4
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import sys
import time
from collections import Counter
from fractions import Fraction
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bench.eval_f1 import align_notes, match_staves, read_case_outputs, reader_tokens, split_by_clef, truth_tokens
from scorereader.classify import ACC_CLASSES, CLASS_TO_ID, _predict_small, extract_patch, load_weights, page_levels
from scorereader.layers import read_layers
from scorereader.meter import _free, bold_commons, time_signs
from scorereader.music import key_alters
from scorereader.starts import read_starts
from tools.synth_glyphs import (
    ITALIC_FONTS,
    NOTO_MUSIC,
    PATCH_SIZE,
    SERIF_FONTS,
    TIME_CLASSES,
    TIME_TO_ID,
    _degrade_scan_levels,
    _draw_font_glyph,
    synthesize_sample,
)
from tools.train_classifier import fit_temperature, fold_conv_bn, make_group_folds, pool_spatial_torch

STEM_SIZE = 32
STEM_SPACES = 4.5
TIME_SIZE = 24

KEY_TO_FIFTHS = {
    'C': 0, 'Am': 0, 'G': 1, 'Em': 1, 'D': 2, 'Bm': 2, 'A': 3, 'F#m': 3,
    'E': 4, 'C#m': 4, 'B': 5, 'G#m': 5, 'F#': 6, 'D#m': 6,
    'F': -1, 'Dm': -1, 'Bb': -2, 'Gm': -2, 'Eb': -3, 'Cm': -3,
    'Ab': -4, 'Fm': -4, 'Db': -5, 'Bbm': -5, 'Gb': -6, 'Ebm': -6,
}
STEP_TO_INDEX = {'C': 0, 'D': 1, 'E': 2, 'F': 3, 'G': 4, 'A': 5, 'B': 6}


def extract_stem_patch(grey: np.ndarray, bare: np.ndarray, staff_rows: list[float], space: float,
                       stem_x: float, stem_end: float, direction: str,
                       levels: tuple[float, float] | None = None) -> np.ndarray:
    """Extracts a canonical (3, 32, 32) patch around a stem tip; down-stems are flipped vertically."""
    patch = extract_patch(grey, bare, staff_rows, space, stem_x, stem_end,
                          size=STEM_SIZE, spaces=STEM_SPACES, levels=levels)
    if direction == 'down':
        patch = patch[:, ::-1, :].copy()
    return patch


class SmallConvNet(nn.Module):
    """Compact 3-conv spatial-pooled classifier for StemNet, TimeNet, and AccNet."""

    def __init__(self, in_ch: int, num_classes: int, channels: tuple[int, int, int] = (20, 40, 64),
                 fc_dim: int = 64) -> None:
        super().__init__()
        c1, c2, c3 = channels
        self.c1 = nn.Conv2d(in_ch, c1, 3, padding=1, bias=True)
        self.b1 = nn.BatchNorm2d(c1)
        self.c2 = nn.Conv2d(c1, c2, 3, padding=1, bias=True)
        self.b2 = nn.BatchNorm2d(c2)
        self.c3 = nn.Conv2d(c2, c3, 3, padding=1, bias=True)
        self.b3 = nn.BatchNorm2d(c3)
        self.drop = nn.Dropout(0.20)
        self.fc1 = nn.Linear(c3 * 6, fc_dim)
        self.fc2 = nn.Linear(fc_dim, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = F.max_pool2d(F.relu(self.b1(self.c1(x))), 2)
        x = F.max_pool2d(F.relu(self.b2(self.c2(x))), 2)
        x = F.relu(self.b3(self.c3(x)))
        feat = pool_spatial_torch(x)
        feat = F.relu(self.fc1(self.drop(feat)))
        return self.fc2(feat)


def export_small_npz(model: SmallConvNet, path: Path, classes: list[str], temperature: float = 1.0) -> float:
    model.eval()
    arrays: dict[str, np.ndarray] = {
        'classes': np.array(classes),
        'temperature': np.array([temperature], dtype=np.float32),
    }
    for idx, (conv, bn) in enumerate(((model.c1, model.b1), (model.c2, model.b2), (model.c3, model.b3)), 1):
        w, b = fold_conv_bn(conv, bn)
        arrays[f'c{idx}w'] = w.astype(np.float16)
        arrays[f'c{idx}b'] = b.astype(np.float32)
    arrays['fc1w'] = model.fc1.weight.detach().cpu().numpy().T.astype(np.float16)
    arrays['fc1b'] = model.fc1.bias.detach().cpu().numpy().astype(np.float32)
    arrays['fc2w'] = model.fc2.weight.detach().cpu().numpy().T.astype(np.float16)
    arrays['fc2b'] = model.fc2.bias.detach().cpu().numpy().astype(np.float32)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **arrays)
    size_kb = path.stat().st_size / 1024.0
    print(f'Exported -> {path} ({size_kb:.1f} KB, T={temperature:.3f})', flush=True)
    return size_kb


def verify_small_parity(model: SmallConvNet, npz_path: Path, temperature: float, sample_x: np.ndarray, name: str) -> float:
    """Verifies pure-NumPy _predict_small matches PyTorch folded probabilities within float16 precision."""
    model.eval()
    x_f32 = sample_x[:128].astype(np.float32) / 255.0
    with torch.no_grad():
        logits = model(torch.from_numpy(x_f32)) / max(0.1, float(temperature))
        pt_probs = F.softmax(logits, dim=1).numpy()
    weights = load_weights(str(npz_path))
    assert weights is not None
    np_probs = _predict_small(x_f32, weights)
    max_diff = float(np.max(np.abs(pt_probs - np_probs)))
    print(f'{name} pure-NumPy parity check (N={len(x_f32)}): max_abs_diff={max_diff:.6f}', flush=True)
    if max_diff > 5e-3:
        raise RuntimeError(f'{name} NumPy parity error too large: {max_diff:.6f}')
    return max_diff


def synthesize_stem(tails: int, rng: np.random.Generator) -> np.ndarray:
    """Synthesizes one canonical upward stem-tip patch (3, 32, 32) with 0, 1, or 2 tails."""
    space = float(rng.uniform(14.0, 30.0))
    side = int(round(7.5 * space))
    cx = side / 2.0 + float(rng.uniform(-0.22 * space, 0.22 * space))
    cy = side / 2.0 + float(rng.uniform(-0.22 * space, 0.22 * space))
    canvas = np.full((side, side), 255, dtype=np.uint8)
    bare = np.full((side, side), 255, dtype=np.uint8)
    staff_mid = cy + float(rng.uniform(-0.5, 3.6) * space)
    rows = [staff_mid + (k - 2) * space for k in range(5)]
    stem_t = max(1, int(round(rng.uniform(0.08, 0.16) * space)))
    line_t = max(1, int(round(rng.uniform(0.08, 0.16) * space)))
    beam_t = max(2, int(round(rng.uniform(0.32, 0.56) * space)))
    local_seed = int(rng.integers(0, 2**31 - 1))

    def draw_it(target: np.ndarray) -> None:
        lr = np.random.default_rng(local_seed)
        stem_len = int(round(lr.uniform(2.4, 3.8) * space))
        cv2.line(target, (int(cx), int(cy)), (int(cx), min(side - 1, int(cy + stem_len))), 0, stem_t)
        hx = int(round(cx - 0.55 * space))
        hy = min(side - 1, int(cy + stem_len))
        cv2.ellipse(target, (hx, hy), (int(0.58 * space), int(0.42 * space)), -20, 0, 360, 0, -1, cv2.LINE_AA)

        if tails == 0:
            neg = str(lr.choice([
                'bare', 'slur_over', 'slur_touch', 'neighbor_stem', 'text_above',
                'text_touch_side', 'ledger_near', 'other_head', 'barline_near',
            ], p=[0.20, 0.14, 0.14, 0.10, 0.10, 0.12, 0.08, 0.07, 0.05]))
            if neg == 'slur_over':
                cv2.ellipse(target, (int(cx + 0.6 * space), int(cy - 0.35 * space)),
                            (int(2.2 * space), int(0.85 * space)), 0, 195, 345, 0, max(1, int(0.15 * space)), cv2.LINE_AA)
            elif neg == 'slur_touch':
                cv2.ellipse(target, (int(cx + 1.1 * space), int(cy + 0.30 * space)),
                            (int(1.6 * space), int(0.65 * space)), 0, 185, 355, 0, max(1, int(0.16 * space)), cv2.LINE_AA)
            elif neg == 'neighbor_stem':
                nx = int(cx + lr.choice([-1, 1]) * lr.uniform(1.4, 2.4) * space)
                cv2.line(target, (nx, int(cy + lr.uniform(-0.5, 0.5) * space)),
                         (nx, min(side - 1, int(cy + 3.2 * space))), 0, stem_t)
            elif neg == 'text_above' and SERIF_FONTS:
                word = str(lr.choice(['Lord', 'the', 'p', 'mf', 'sing', 'God']))
                _draw_font_glyph(target, word, str(lr.choice(SERIF_FONTS)),
                                 int(round(lr.uniform(1.0, 1.5) * space)), cx, cy - lr.uniform(0.7, 1.4) * space)
            elif neg == 'text_touch_side' and SERIF_FONTS:
                word = str(lr.choice(['a', 'o', 'e', 'the', 'and', 'to', 'us', 'is']))
                tx = cx + float(lr.choice([-1, 1]) * lr.uniform(0.35, 0.95) * space)
                ty = cy + float(lr.uniform(-0.25, 0.75) * space)
                _draw_font_glyph(target, word, str(lr.choice(SERIF_FONTS)),
                                 int(round(lr.uniform(1.0, 1.6) * space)), tx, ty)
            elif neg == 'ledger_near':
                for k in range(int(lr.integers(1, 3))):
                    ly = int(round(cy + lr.uniform(-0.3, 1.2) * space + k * space))
                    cv2.line(target, (int(cx - 1.2 * space), ly), (int(cx + 0.6 * space), ly), 0, line_t)
            elif neg == 'other_head':
                ox = int(round(cx + lr.uniform(-0.4, 0.9) * space))
                oy = int(round(cy + lr.uniform(0.4, 1.4) * space))
                cv2.ellipse(target, (ox, oy), (int(0.58 * space), int(0.42 * space)), -20, 0, 360, 0, -1, cv2.LINE_AA)
            elif neg == 'barline_near':
                bx = int(round(cx + lr.choice([-1, 1]) * lr.uniform(0.6, 1.4) * space))
                cv2.line(target, (bx, int(rows[0])), (bx, int(rows[4])), 0, stem_t)

        elif tails in (1, 2):
            mode = str(lr.choice(['beam_right', 'beam_left', 'beam_both', 'flag', 'beam_stub'],
                                 p=[0.28, 0.24, 0.24, 0.18, 0.06] if tails == 2 else [0.30, 0.25, 0.25, 0.20, 0.0]))
            slope = float(lr.uniform(-0.22, 0.22))
            if mode == 'flag':
                for k in range(tails):
                    y0 = cy + k * 0.72 * space
                    pts = np.array([
                        [int(cx), int(y0)],
                        [int(cx + 0.72 * space), int(y0 + 0.52 * space)],
                        [int(cx + 0.90 * space), int(y0 + 1.22 * space)],
                        [int(cx + 0.52 * space), int(y0 + 1.82 * space)],
                    ], np.int32)
                    cv2.polylines(target, [pts], False, 0, max(2, int(round(0.24 * space))), cv2.LINE_AA)
            else:
                x_left = int(cx - 2.3 * space) if mode in ('beam_left', 'beam_both', 'beam_stub') else int(cx)
                x_right = int(cx + 2.3 * space) if mode in ('beam_right', 'beam_both', 'beam_stub') else int(cx)
                for k in range(tails):
                    y_off = k * (beam_t + max(2, int(round(0.32 * space))))
                    xl, xr = x_left, x_right
                    if mode == 'beam_stub' and k == 1:
                        if lr.random() < 0.5:
                            xl, xr = int(cx), int(cx + 0.95 * space)
                        else:
                            xl, xr = int(cx - 0.95 * space), int(cx)
                    y_l = int(round(cy + y_off + slope * (xl - cx)))
                    y_r = int(round(cy + y_off + slope * (xr - cx)))
                    pts = np.array([
                        [xl, y_l], [xr, y_r], [xr, y_r + beam_t], [xl, y_l + beam_t],
                    ], np.int32)
                    cv2.fillPoly(target, [pts], 0)
                nx = int(cx + (1.8 * space if mode in ('beam_right', 'beam_both', 'beam_stub') else -1.8 * space))
                ny = int(round(cy + slope * (nx - cx)))
                cv2.line(target, (nx, ny), (nx, min(side - 1, int(ny + 3.0 * space))), 0, stem_t)

    draw_it(bare)
    draw_it(canvas)
    line_grey = int(rng.uniform(0, 75))
    for r in rows:
        ry = int(round(r))
        if 0 <= ry < side:
            cv2.line(canvas, (0, ry), (side - 1, ry), line_grey, line_t)
    degraded, bare_mask, levels = _degrade_scan_levels(canvas, rng, bare=bare)
    assert bare_mask is not None
    return extract_patch(degraded, bare_mask, rows, space, cx, cy, size=STEM_SIZE, spaces=STEM_SPACES, levels=levels)


def extract_dev_stems(manifest_path: Path, res_dir: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Extracts verified exact-matched untied stem-tip crops strictly from Clean Dev pages."""
    if 'holdout' in manifest_path.name.lower() or 'clean_all' in manifest_path.name.lower():
        sys.exit('REFUSED: never extract StemNet crops from holdout or combined manifest.')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('split') != 'clean_dev':
        sys.exit(f"REFUSED: expected manifest split 'clean_dev', got {manifest.get('split')!r}.")
    truth_dir = Path(manifest['truth_dir'])
    xs, ys, gs = [], [], []
    for case in manifest['cases']:
        cid = case['id']
        base_id = case.get('base_id', cid.split('--')[0])
        tpath = truth_dir / f'{cid}.json'
        if not tpath.exists():
            continue
        truth = json.loads(tpath.read_text(encoding='utf-8'))
        out = read_case_outputs(res_dir, case)
        layout = case['layout']
        if layout == [['melody', 'ison']] and len(out['notes']) == 2:
            layout = [['melody'], ['ison']]
        staves = split_by_clef(out['notes'], len(layout))
        actual = [reader_tokens(s) for s in staves]
        expected = [truth_tokens(truth, parts) for parts in layout]
        chosen = match_staves(expected, actual)

        exact_matched: dict[int, Counter] = {}
        for row, (_, exp_tok) in enumerate(zip(layout, expected)):
            idx = chosen[row]
            if idx is None:
                continue
            rd = actual[idx]
            _, pairs = align_notes(exp_tok, rd)
            mk = exact_matched.setdefault(idx, Counter())
            for r, k in pairs:
                if r is not None and k is not None and exp_tok[r][2] == rd[k][2] and exp_tok[r][1] == rd[k][1]:
                    mk[(rd[k][2], rd[k][1])] += 1

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
            lay = json.loads(lay_p.read_text(encoding='utf-8'))
            nj = json.loads(notes_p.read_text(encoding='utf-8'))
            places = lay.get('clean_page') or []
            if not places:
                continue
            layers = read_layers(grey, places)
            bare = layers['bare']
            staves_info = layers['staves']
            levels = page_levels(grey)
            for note in nj.get('notes', []):
                if note.get('tie_start') or note.get('tie_stop'):
                    continue
                mark = note.get('mark') or {}
                stem_info = mark.get('stem')
                if not stem_info or mark.get('hollow'):
                    continue
                s_idx = note.get('staff')
                if s_idx is None or not (0 <= s_idx < len(staves_info)):
                    continue
                staff = staves_info[s_idx]
                nlen = Fraction(note['length']).limit_denominator(192)
                key = (int(note['midi']), nlen)
                if exact_matched.get(staff['number'], Counter()).get(key, 0) <= 0:
                    continue
                exact_matched[staff['number']][key] -= 1
                if nlen in (Fraction(1), Fraction(3, 2), Fraction(2, 3)):
                    lbl = 0
                elif nlen in (Fraction(1, 2), Fraction(3, 4), Fraction(1, 3)):
                    lbl = 1
                elif nlen in (Fraction(1, 4), Fraction(3, 8), Fraction(1, 6)):
                    lbl = 2
                else:
                    continue
                direction = 'up' if float(stem_info['end']) < float(mark.get('y', staff['rows'][2])) else 'down'
                p = extract_stem_patch(grey, bare, staff['rows'], staff['space'],
                                       float(stem_info['x']), float(stem_info['end']), direction, levels=levels)
                xs.append((p * 255.0).round().astype(np.uint8))
                ys.append(lbl)
                gs.append(base_id)
    if not xs:
        return np.zeros((0, 3, STEM_SIZE, STEM_SIZE), np.uint8), np.zeros(0, np.int64), np.array([], dtype=str)
    return np.stack(xs, axis=0), np.array(ys, dtype=np.int64), np.array(gs)


def _extract_left_neg_one_case(task: tuple[dict, str, str, int, int]) -> tuple[list[np.ndarray], list[str]]:
    """Extracts hard left-of-head non-accidental patches for one Clean Dev case."""
    case, truth_dir_s, res_dir_s, max_per_page, seed = task
    cid = case['id']
    base_id = case.get('base_id', cid.split('--')[0])
    tpath = Path(truth_dir_s) / f'{cid}.json'
    res_dir = Path(res_dir_s)
    if not tpath.exists():
        return [], []
    truth = json.loads(tpath.read_text(encoding='utf-8'))
    truth_fifths = KEY_TO_FIFTHS.get(str(truth.get('key', '')))
    key_map = key_alters(truth_fifths) if truth_fifths is not None else {}
    rng = np.random.default_rng(seed)

    xs: list[np.ndarray] = []
    gs: list[str] = []
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
        lay = json.loads(lay_p.read_text(encoding='utf-8'))
        nj = json.loads(notes_p.read_text(encoding='utf-8'))
        places = lay.get('clean_page') or []
        if not places:
            continue
        layers = read_layers(grey, places)
        bare = layers['bare']
        staves_info = layers['staves']
        levels = page_levels(grey)
        h_img, w_img = bare.shape

        # Collect all notes with a printed accidental on each staff so we never sample near them.
        acc_spots: dict[int, list[tuple[float, float]]] = {i: [] for i in range(len(staves_info))}
        cands: list[tuple[int, float, float]] = []
        for note in nj.get('notes', []):
            si = note.get('staff')
            if si is None or not (0 <= si < len(staves_info)):
                continue
            mk = note.get('mark') or {}
            nx = float(note['x'])
            ny = float(mk.get('y', staves_info[si]['rows'][2]))
            sp = float(staves_info[si]['space'])
            step_idx = STEP_TO_INDEX.get(str(note.get('step', '')).upper())
            note_alt = int(note.get('alter', 0))
            key_alt = key_map.get(step_idx, 0) if step_idx is not None else 0
            if mk.get('sign') is not None or note_alt != key_alt:
                acc_spots[si].append((nx - 1.1 * sp, ny))
                continue
            if nx < staves_info[si]['x0'] + 4.5 * sp:
                continue
            for off in (1.05, 1.45):
                cx = nx - off * sp
                cy = ny
                # Keep hard negatives holding bare ink plus ~15% sparse/clean-staff left-of-head patches.
                x0 = max(0, int(cx - 0.65 * sp))
                x1 = min(w_img, int(cx + 0.65 * sp))
                y0 = max(0, int(cy - 0.85 * sp))
                y1 = min(h_img, int(cy + 0.85 * sp))
                if x1 > x0 + 3 and y1 > y0 + 3:
                    dens = float((bare[y0:y1, x0:x1] > 0).mean())
                    if dens >= 0.05 or rng.random() < 0.04:
                        cands.append((si, cx, cy))

        rng.shuffle(cands)
        taken = 0
        for si, cx, cy in cands:
            if taken >= max_per_page:
                break
            sp = float(staves_info[si]['space'])
            if any(abs(ax - cx) < 1.3 * sp and abs(ay - cy) < 1.3 * sp for ax, ay in acc_spots[si]):
                continue
            p = extract_patch(grey, bare, staves_info[si]['rows'], sp, cx, cy,
                              size=PATCH_SIZE, levels=levels)
            xs.append((p * 255.0).round().astype(np.uint8))
            gs.append(base_id)
            taken += 1
    return xs, gs


def extract_dev_left_negatives(manifest_path: Path, res_dir: Path, max_per_page: int = 28) -> tuple[np.ndarray, np.ndarray]:
    """Extracts hard left-of-head non-accidental negatives strictly from Clean Dev pages."""
    if 'holdout' in manifest_path.name.lower() or 'clean_all' in manifest_path.name.lower():
        sys.exit('REFUSED: never extract AccNet negatives from holdout or combined manifest.')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('split') != 'clean_dev':
        sys.exit(f"REFUSED: expected manifest split 'clean_dev', got {manifest.get('split')!r}.")
    tasks = [
        (case, str(manifest['truth_dir']), str(res_dir), max_per_page, 9001 + i)
        for i, case in enumerate(manifest['cases'])
    ]
    xs: list[np.ndarray] = []
    gs: list[str] = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for px, pg in pool.map(_extract_left_neg_one_case, tasks):
            xs.extend(px)
            gs.extend(pg)
    if not xs:
        return np.zeros((0, 3, PATCH_SIZE, PATCH_SIZE), np.uint8), np.array([], dtype=str)
    return np.stack(xs, axis=0), np.array(gs)


def _normalize_time_crop(crop_f32: np.ndarray) -> np.ndarray:
    """Centers a cropped [0, 1] time-signature glyph inside (1, 24, 24) uint8 matching classify_time_crop."""
    h, w = crop_f32.shape
    scale = (TIME_SIZE - 4) / max(h, w)
    nh, nw = max(1, int(round(h * scale))), max(1, int(round(w * scale)))
    resized = cv2.resize(crop_f32, (nw, nh), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)
    out = np.zeros((TIME_SIZE, TIME_SIZE), dtype=np.float32)
    y0, x0 = (TIME_SIZE - nh) // 2, (TIME_SIZE - nw) // 2
    out[y0:y0 + nh, x0:x0 + nw] = resized
    return (out[None, :, :] * 255.0).round().astype(np.uint8)


def _bridge_staff_rows_only(mask: np.ndarray, row_positions: list[float], thick: float) -> np.ndarray:
    """Bridges vertical breaks ONLY inside narrow bands around staff rows (never global morph-close)."""
    out = mask.copy()
    bh = max(3, int(round(thick + 3))) | 1
    closed = cv2.morphologyEx(np.ascontiguousarray(mask), cv2.MORPH_CLOSE, np.ones((bh, 1), np.uint8))
    half = bh // 2 + 1
    h = mask.shape[0]
    for r in row_positions:
        ry = int(round(r))
        r0, r1 = max(0, ry - half), min(h, ry + half + 1)
        if r1 > r0:
            out[r0:r1] = closed[r0:r1]
    return out


def _draw_engraved_music_digit(canvas: np.ndarray, cls_name: str, cx: float, cy: float,
                               h_px: float, rng: np.random.Generator) -> None:
    """Draws bold music-engraving digits (ball-terminal 2/3/6/9, heavy 4, bold C/cut)."""
    w_px = h_px * float(rng.uniform(0.62, 0.85))
    if cls_name == '12':
        w_px = h_px * float(rng.uniform(1.05, 1.35))
    t = max(3, int(round(h_px * rng.uniform(0.14, 0.22))))
    x0, x1 = cx - 0.5 * w_px, cx + 0.5 * w_px
    y0, y1 = cy - 0.5 * h_px, cy + 0.5 * h_px

    if cls_name == '3':
        cv2.ellipse(canvas, (int(cx + 0.04 * w_px), int(y0 + 0.26 * h_px)),
                    (int(0.42 * w_px), int(0.24 * h_px)), 0, -165, 95, 0, t, cv2.LINE_AA)
        cv2.ellipse(canvas, (int(cx + 0.04 * w_px), int(y0 + 0.74 * h_px)),
                    (int(0.44 * w_px), int(0.26 * h_px)), 0, -95, 165, 0, t, cv2.LINE_AA)
        br = max(2, int(round(h_px * rng.uniform(0.11, 0.19))))
        cv2.circle(canvas, (int(x0 + 0.18 * w_px), int(y0 + 0.23 * h_px)), br, 0, -1, cv2.LINE_AA)
        cv2.circle(canvas, (int(x0 + 0.18 * w_px), int(y0 + 0.77 * h_px)), br, 0, -1, cv2.LINE_AA)
        cv2.line(canvas, (int(cx - 0.16 * w_px), int(cy)), (int(cx + 0.24 * w_px), int(cy)), 0, max(2, int(0.95 * t)), cv2.LINE_AA)
        if rng.random() < 0.35:
            cv2.ellipse(canvas, (int(x0 + 0.17 * w_px), int(y0 + 0.34 * h_px)), (int(0.14 * w_px), int(0.11 * h_px)), 0, 0, 360, 0, -1, cv2.LINE_AA)
            cv2.ellipse(canvas, (int(x0 + 0.17 * w_px), int(y0 + 0.66 * h_px)), (int(0.14 * w_px), int(0.11 * h_px)), 0, 0, 360, 0, -1, cv2.LINE_AA)
    elif cls_name == '4':
        stem_x = int(round(cx + rng.uniform(0.08, 0.22) * w_px))
        bar_y = int(round(y0 + rng.uniform(0.58, 0.70) * h_px))
        apex_x = int(round(stem_x - rng.uniform(0.0, 0.14) * w_px))
        cv2.line(canvas, (apex_x, int(y0 + 0.04 * h_px)), (int(x0 + 0.04 * w_px), bar_y), 0, t, cv2.LINE_AA)
        cv2.line(canvas, (int(x0 + 0.02 * w_px), bar_y), (int(x1 - 0.02 * w_px), bar_y), 0, t, cv2.LINE_AA)
        cv2.line(canvas, (stem_x, int(y0 + 0.18 * h_px)), (stem_x, int(y1 - 0.04 * h_px)), 0, t, cv2.LINE_AA)
        if rng.random() < 0.45:
            cv2.line(canvas, (int(stem_x - 0.22 * w_px), int(y1 - 0.04 * h_px)),
                     (int(stem_x + 0.22 * w_px), int(y1 - 0.04 * h_px)), 0, max(2, t // 2), cv2.LINE_AA)
        if rng.random() < 0.35:
            pts = np.array([[apex_x, int(y0 + 0.22 * h_px)], [int(x0 + 0.18 * w_px), bar_y], [stem_x, bar_y]], np.int32)
            cv2.fillPoly(canvas, [pts], 0)
    elif cls_name == '2':
        cv2.ellipse(canvas, (int(cx), int(y0 + 0.28 * h_px)),
                    (int(0.42 * w_px), int(0.24 * h_px)), 0, -175, 45, 0, t, cv2.LINE_AA)
        br = max(2, int(round(h_px * rng.uniform(0.10, 0.15))))
        cv2.circle(canvas, (int(x0 + 0.18 * w_px), int(y0 + 0.26 * h_px)), br, 0, -1, cv2.LINE_AA)
        cv2.line(canvas, (int(x1 - 0.14 * w_px), int(y0 + 0.36 * h_px)),
                 (int(x0 + 0.08 * w_px), int(y1 - 0.10 * h_px)), 0, t, cv2.LINE_AA)
        cv2.line(canvas, (int(x0 + 0.04 * w_px), int(y1 - 0.08 * h_px)),
                 (int(x1 - 0.04 * w_px), int(y1 - 0.08 * h_px)), 0, int(1.15 * t), cv2.LINE_AA)
    elif cls_name == '6':
        cv2.ellipse(canvas, (int(cx + 0.02 * w_px), int(cy)),
                    (int(0.44 * w_px), int(0.46 * h_px)), 0, 95, 295, 0, t, cv2.LINE_AA)
        cv2.ellipse(canvas, (int(cx + 0.02 * w_px), int(y0 + 0.68 * h_px)),
                    (int(0.42 * w_px), int(0.28 * h_px)), 0, 0, 360, 0, t, cv2.LINE_AA)
        br = max(2, int(round(h_px * rng.uniform(0.09, 0.14))))
        cv2.circle(canvas, (int(x1 - 0.18 * w_px), int(y0 + 0.20 * h_px)), br, 0, -1, cv2.LINE_AA)
    elif cls_name == '8':
        cv2.ellipse(canvas, (int(cx), int(y0 + 0.26 * h_px)),
                    (int(0.38 * w_px), int(0.23 * h_px)), 0, 0, 360, 0, t, cv2.LINE_AA)
        cv2.ellipse(canvas, (int(cx), int(y0 + 0.72 * h_px)),
                    (int(0.44 * w_px), int(0.26 * h_px)), 0, 0, 360, 0, t, cv2.LINE_AA)
    elif cls_name == '9':
        cv2.ellipse(canvas, (int(cx - 0.02 * w_px), int(cy)),
                    (int(0.44 * w_px), int(0.46 * h_px)), 0, -85, 115, 0, t, cv2.LINE_AA)
        cv2.ellipse(canvas, (int(cx - 0.02 * w_px), int(y0 + 0.32 * h_px)),
                    (int(0.42 * w_px), int(0.28 * h_px)), 0, 0, 360, 0, t, cv2.LINE_AA)
        br = max(2, int(round(h_px * rng.uniform(0.09, 0.14))))
        cv2.circle(canvas, (int(x0 + 0.18 * w_px), int(y1 - 0.20 * h_px)), br, 0, -1, cv2.LINE_AA)
    elif cls_name in ('C', 'cut'):
        ch = h_px * float(rng.uniform(0.92, 1.18))
        cw = ch * float(rng.uniform(0.60, 0.96))
        t_c = max(2, int(round(ch * rng.uniform(0.10, 0.21))))
        cv2.ellipse(canvas, (int(cx + 0.04 * cw), int(cy)),
                    (int(0.46 * cw), int(0.46 * ch)), 0, 42, 318, 0, t_c, cv2.LINE_AA)
        if rng.random() < 0.75:
            br = max(2, int(round(ch * rng.uniform(0.10, 0.17))))
            cv2.circle(canvas, (int(cx + 0.34 * cw), int(cy - 0.26 * ch)), br, 0, -1, cv2.LINE_AA)
        if cls_name == 'cut':
            sx = int(round(cx + rng.uniform(-0.12, 0.14) * cw))
            st = max(2, int(round(ch * rng.uniform(0.08, 0.16))))
            cv2.line(canvas, (sx, int(cy - 0.68 * ch)), (sx, int(cy + 0.68 * ch)), 0, st, cv2.LINE_AA)


def synthesize_time_glyph(cls_name: str, rng: np.random.Generator) -> np.ndarray:
    """Synthesizes one (1, 24, 24) time-signature patch with realistic staff-row-only breaks."""
    space = float(rng.uniform(18.0, 28.0))
    canvas_s = 112
    canvas = np.full((canvas_s, canvas_s), 255, dtype=np.uint8)
    cx, cy = canvas_s / 2.0, canvas_s / 2.0
    ang = float(rng.uniform(-4.0, 4.0))
    digit_h = 2.0 * space
    line_t = max(2, int(round(rng.uniform(0.09, 0.18) * space)))

    if cls_name in ('2', '3', '4', '6', '8', '9', '12'):
        if cls_name != '12' and rng.random() < 0.45:
            _draw_engraved_music_digit(canvas, cls_name, cx, cy, digit_h * float(rng.uniform(0.92, 1.08)), rng)
        else:
            font = str(rng.choice(SERIF_FONTS))
            px = int(round(digit_h * rng.uniform(1.15, 1.48)))
            sx = float(rng.uniform(0.75, 1.18))
            _draw_font_glyph(canvas, cls_name, font, px, cx, cy, ang, scale_x=sx)
            if rng.random() < 0.45:
                k = int(rng.choice([2, 3]))
                canvas = cv2.erode(canvas, np.ones((k, k), np.uint8))
    elif cls_name == 'C':
        roll = rng.random()
        if roll < 0.40 and Path(NOTO_MUSIC).exists():
            _draw_font_glyph(canvas, '\U0001D134', NOTO_MUSIC, int(round(space * rng.uniform(3.4, 4.4))), cx, cy, ang)
        elif roll < 0.78:
            _draw_engraved_music_digit(canvas, 'C', cx, cy, digit_h * float(rng.uniform(0.90, 1.10)), rng)
        else:
            _draw_font_glyph(canvas, 'C', str(rng.choice(SERIF_FONTS)), int(round(digit_h * rng.uniform(1.15, 1.45))), cx, cy, ang)
    elif cls_name == 'cut':
        roll = rng.random()
        if roll < 0.35 and Path(NOTO_MUSIC).exists():
            _draw_font_glyph(canvas, '\U0001D135', NOTO_MUSIC, int(round(space * rng.uniform(3.4, 4.4))), cx, cy, ang)
        elif roll < 0.75:
            _draw_engraved_music_digit(canvas, 'cut', cx, cy, digit_h * float(rng.uniform(0.90, 1.10)), rng)
        else:
            _draw_font_glyph(canvas, 'C', str(rng.choice(SERIF_FONTS)), int(round(digit_h * rng.uniform(1.15, 1.45))), cx, cy, ang)
            cv2.line(canvas, (int(cx), int(cy - 1.45 * space)), (int(cx), int(cy + 1.45 * space)), 0, max(2, int(0.14 * space)))
    else:
        kind = str(rng.choice(['sharp', 'flat', 'natural', 'head', 'bar', 'letter', 'rest_q', 'rest_e']))
        if kind == 'sharp':
            _draw_font_glyph(canvas, '\u266F', NOTO_MUSIC, int(3.0 * space), cx, cy, ang)
        elif kind == 'flat':
            _draw_font_glyph(canvas, '\u266D', NOTO_MUSIC, int(3.0 * space), cx, cy, ang)
        elif kind == 'natural':
            _draw_font_glyph(canvas, '\u266E', NOTO_MUSIC, int(3.0 * space), cx, cy, ang)
        elif kind == 'head':
            cv2.ellipse(canvas, (int(cx), int(cy)), (int(0.65 * space), int(0.45 * space)), -20, 0, 360, 0, -1)
            cv2.line(canvas, (int(cx + 0.58 * space), int(cy - 2.0 * space)), (int(cx + 0.58 * space), int(cy)), 0, 3)
        elif kind == 'bar':
            cv2.line(canvas, (int(cx), int(cy - 1.8 * space)), (int(cx), int(cy + 1.8 * space)), 0, int(rng.integers(2, 6)))
        elif kind == 'rest_q':
            _draw_font_glyph(canvas, '\U0001D13D', NOTO_MUSIC, int(3.5 * space), cx, cy, ang)
        elif kind == 'rest_e':
            _draw_font_glyph(canvas, '\U0001D13E', NOTO_MUSIC, int(3.2 * space), cx, cy, ang)
        else:
            _draw_font_glyph(canvas, str(rng.choice(list('ABDFGHLMPST'))), str(rng.choice(ITALIC_FONTS)), int(2.0 * space), cx, cy, ang)

    staff_rows = [cy - space, cy, cy + space]
    with_lines = canvas.copy()
    for ry_f in staff_rows:
        ry = int(round(ry_f))
        if 0 <= ry < canvas_s:
            cv2.line(with_lines, (0, ry), (canvas_s - 1, ry), int(rng.uniform(0, 60)), line_t)

    degraded, _, (dark, paper) = _degrade_scan_levels(with_lines, rng, bare=None)
    thresh = dark + 0.55 * (paper - dark)
    ink = (degraded < thresh).astype(np.uint8)

    limit = int(round(line_t + max(2.0, 0.5 * line_t)))
    tall = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((limit + 1, 1), np.uint8))
    thin = ink & (1 - tall)
    lines_mask = np.zeros_like(ink)
    half = int(np.ceil(line_t / 2.0 + 2))
    for ry_f in staff_rows:
        ry = int(round(ry_f))
        lines_mask[max(0, ry - half):min(canvas_s, ry + half + 1), :] |= thin[max(0, ry - half):min(canvas_s, ry + half + 1), :]
    free = ink & (1 - lines_mask)

    if rng.random() < 0.85:
        free = _bridge_staff_rows_only(free, staff_rows, float(line_t))

    ys_orig, xs_orig = np.nonzero(canvas < 220)
    if len(ys_orig) < 6:
        return np.zeros((1, TIME_SIZE, TIME_SIZE), dtype=np.uint8)
    gx0 = max(0, int(xs_orig.min()) - 2)
    gx1 = min(canvas_s, int(xs_orig.max()) + 3)
    gy0 = max(0, int(ys_orig.min()) - 2)
    gy1 = min(canvas_s, int(ys_orig.max()) + 3)

    if rng.random() < 0.78:
        sub = free[gy0:gy1, gx0:gx1].astype(np.float32)
    else:
        sub_g = np.clip((paper - degraded[gy0:gy1, gx0:gx1].astype(np.float32)) / max(25.0, paper - dark), 0.0, 1.0)
        sub = sub_g * (free[gy0:gy1, gx0:gx1] > 0).astype(np.float32)

    ys, xs = np.nonzero(sub > 0.15)
    if len(ys) < 6:
        return np.zeros((1, TIME_SIZE, TIME_SIZE), dtype=np.uint8)
    crop = sub[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return _normalize_time_crop(crop)


def extract_dev_time_crops(manifest_path: Path, res_dir: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Extracts verified real Clean Dev time-signature crops strictly from clean_dev.json."""
    if 'holdout' in manifest_path.name.lower() or 'clean_all' in manifest_path.name.lower():
        sys.exit('REFUSED: never extract TimeNet crops from holdout or combined manifest.')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('split') != 'clean_dev':
        sys.exit(f"REFUSED: expected manifest split 'clean_dev', got {manifest.get('split')!r}.")

    xs, ys, gs = [], [], []
    for case in manifest['cases']:
        meter = str(case.get('meter') or 'none').strip()
        if meter in ('none', ''):
            continue
        cid = case['id']
        base_id = case.get('base_id', cid.split('--')[0])
        clean_p = res_dir / f'{cid}-p1.clean.png'
        lay_p = res_dir / f'{cid}-p1.layout.json'
        if not (clean_p.exists() and lay_p.exists()):
            continue
        grey = cv2.imread(str(clean_p), cv2.IMREAD_GRAYSCALE)
        if grey is None:
            continue
        lay = json.loads(lay_p.read_text(encoding='utf-8'))
        places = lay.get('clean_page') or []
        if not places:
            continue
        layers = read_layers(grey, places)
        beg = read_starts(layers)
        free = _free(layers)
        staves = layers['staves']
        sys0 = [i for i, st in enumerate(staves) if st['system'] == 0]
        for idx in sys0:
            staff = staves[idx]
            sp = float(staff['space'])
            rows = staff['rows']
            sign = beg['starts'][idx].get('time')
            if not sign:
                key_r = beg['starts'][idx].get('end', beg['starts'][idx]['x1'])
                cands = bold_commons(layers, staff, key_r - 1.5 * sp, max(beg['ends'][idx], key_r) + 5.5 * sp)
                cands += time_signs(layers, staff, beg['starts'][idx]['x1'] - 0.3 * sp, max(beg['ends'][idx], key_r) + 5.5 * sp)
                sign = cands[0] if cands else None
            if not sign:
                continue
            h, w = free.shape
            if meter in ('C', 'C|'):
                lbl = 'cut' if meter == 'C|' else 'C'
                pad_l = int(0.8 * sp) if meter == 'C|' else 2
                x0 = max(0, int(sign['x0']) - pad_l)
                x1 = min(w, int(sign['x1']) + 3)
                y0 = max(0, int(rows[0] - 0.7 * sp))
                y1 = min(h, int(rows[4] + 0.7 * sp) + 1)
                if x1 > x0 + 3 and y1 > y0 + 3:
                    sub = _bridge_staff_rows_only(free[y0:y1, x0:x1], [r - y0 for r in rows], float(staff['thick']))
                    ys_nz, xs_nz = np.nonzero(sub)
                    if len(ys_nz) >= 10:
                        xs.append(_normalize_time_crop(sub[ys_nz.min():ys_nz.max() + 1, xs_nz.min():xs_nz.max() + 1].astype(np.float32)))
                        ys.append(TIME_TO_ID[lbl])
                        gs.append(base_id)
            elif '/' in meter:
                num_s, den_s = meter.split('/', 1)
                if num_s not in TIME_TO_ID or den_s not in TIME_TO_ID:
                    continue
                x0 = max(0, int(sign['x0']) - 1)
                x1 = min(w, int(sign['x1']) + 2)
                y_top = max(0, int(rows[0] - 0.35 * sp))
                y_mid = int(round(rows[2]))
                y_bot = min(h, int(rows[4] + 0.35 * sp) + 1)
                if x1 > x0 + 3 and y_mid > y_top + 3 and y_bot > y_mid + 3:
                    for lbl_s, m_raw, y_off in ((num_s, free[y_top:y_mid, x0:x1], y_top),
                                                (den_s, free[y_mid:y_bot, x0:x1], y_mid)):
                        sub = _bridge_staff_rows_only(m_raw, [r - y_off for r in rows], float(staff['thick']))
                        ys_nz, xs_nz = np.nonzero(sub)
                        if len(ys_nz) >= 8:
                            xs.append(_normalize_time_crop(sub[ys_nz.min():ys_nz.max() + 1, xs_nz.min():xs_nz.max() + 1].astype(np.float32)))
                            ys.append(TIME_TO_ID[lbl_s])
                            gs.append(base_id)
    if not xs:
        return np.zeros((0, 1, TIME_SIZE, TIME_SIZE), np.uint8), np.zeros(0, np.int64), np.array([], dtype=str)
    return np.stack(xs, axis=0), np.array(ys, dtype=np.int64), np.array(gs)


def predict_small_logits(model: SmallConvNet, X: np.ndarray, batch_size: int = 512) -> np.ndarray:
    model.eval()
    outs = []
    with torch.no_grad():
        for i in range(0, len(X), batch_size):
            bx = torch.from_numpy(X[i:i + batch_size]).float() / 255.0
            outs.append(model(bx).numpy())
    return np.concatenate(outs, axis=0) if outs else np.zeros((0, model.fc2.out_features), np.float32)


def _augment_small(bx: torch.Tensor, in_ch: int) -> torch.Tensor:
    n, c, h, w = bx.shape
    pad = 2 if in_ch == 3 else 1
    padded = F.pad(bx, (pad, pad, pad, pad), mode='constant', value=0.0)
    out = torch.empty_like(bx)
    span = 2 * pad + 1
    sy_all = torch.randint(0, span, (n,))
    sx_all = torch.randint(0, span, (n,))
    for i in range(n):
        sy, sx = int(sy_all[i]), int(sx_all[i])
        out[i] = padded[i, :, sy:sy + h, sx:sx + w]
    if in_ch == 3:
        gain = torch.empty((n, 1, 1), dtype=bx.dtype).uniform_(0.80, 1.20)
        out[:, 0] = torch.clamp(out[:, 0] * gain, 0.0, 1.0)
    return out


def train_small(X: np.ndarray, Y: np.ndarray, in_ch: int, num_classes: int, epochs: int, seed: int,
                X_val: np.ndarray | None = None, Y_val: np.ndarray | None = None,
                weight_pow: float = 0.22, channels: tuple[int, int, int] = (20, 40, 64),
                fc_dim: int = 64) -> tuple[SmallConvNet, np.ndarray | None]:
    torch.manual_seed(seed)
    model = SmallConvNet(in_ch, num_classes, channels=channels, fc_dim=fc_dim)
    counts = np.bincount(Y, minlength=num_classes).astype(np.float32)
    w = np.where(counts > 0, (counts.max() / np.maximum(counts, 1.0)) ** weight_pow, 1.0)
    crit = nn.CrossEntropyLoss(weight=torch.tensor(w / w.mean(), dtype=torch.float32), label_smoothing=0.02)
    opt = torch.optim.AdamW(model.parameters(), lr=2.5e-3, weight_decay=3e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    loader = DataLoader(TensorDataset(torch.from_numpy(X), torch.from_numpy(Y.astype(np.int64))),
                        batch_size=256, shuffle=True)
    for ep in range(epochs):
        model.train()
        tot = 0.0
        for bx, by in loader:
            bx = _augment_small(bx.float() / 255.0, in_ch)
            opt.zero_grad(set_to_none=True)
            loss = crit(model(bx), by)
            loss.backward()
            opt.step()
            tot += float(loss.item())
        sched.step()
        if (ep + 1) % 4 == 0 or ep + 1 == epochs:
            msg = f'  epoch {ep + 1:2d}/{epochs} loss={tot / max(1, len(loader)):.4f}'
            if X_val is not None and len(X_val):
                vl = predict_small_logits(model, X_val)
                msg += f' val_acc={(vl.argmax(1) == Y_val).mean():.4f}'
            print(msg, flush=True)
    val_out = predict_small_logits(model, X_val) if (X_val is not None and len(X_val)) else None
    return model, val_out


def _report_oof(title: str, logits: np.ndarray, labels: np.ndarray, class_names: list[str],
                fonts: np.ndarray | None = None) -> None:
    preds = logits.argmax(1)
    acc = float((preds == labels).mean())
    print(f'=== {title}: {acc:.4%} ({len(labels)} crops) ===', flush=True)
    for cid in sorted(set(labels.tolist())):
        m = labels == cid
        p = preds == cid
        tp = int((m & p).sum())
        rec = tp / max(1, int(m.sum()))
        prec = tp / max(1, int(p.sum()))
        f1 = 2 * prec * rec / max(1e-9, prec + rec)
        print(f'  {class_names[cid]:10s}: rec={rec:7.2%} prec={prec:7.2%} f1={f1:7.2%} ({int(m.sum()):5d} crops)', flush=True)
    if fonts is not None and len(fonts) == len(labels):
        for font in sorted(set(fonts.tolist())):
            fm = fonts == font
            print(f'  font {font:10s}: {(preds[fm] == labels[fm]).mean():7.2%} ({int(fm.sum()):5d} crops)', flush=True)


def _build_acc_split(X_sym: np.ndarray, Y_sym: np.ndarray, G_sym: np.ndarray, F_sym: np.ndarray | None,
                     neg_cap: int, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray | None]:
    """Maps 19-class symbol crops to 4-class AccNet labels (0: none, 1: sharp, 2: flat, 3: natural)."""
    acc_map = {
        CLASS_TO_ID['acc_sharp']: 1,
        CLASS_TO_ID['acc_flat']: 2,
        CLASS_TO_ID['acc_natural']: 3,
    }
    pos_idx = np.where(np.isin(Y_sym, list(acc_map.keys())))[0]
    neg_idx = np.where(~np.isin(Y_sym, list(acc_map.keys())))[0]
    rng = np.random.default_rng(seed)
    if len(neg_idx) > neg_cap:
        neg_idx = rng.choice(neg_idx, size=neg_cap, replace=False)
    sel = np.concatenate([pos_idx, neg_idx])
    X_out = X_sym[sel]
    Y_out = np.array([acc_map.get(int(y), 0) for y in Y_sym[sel]], dtype=np.int64)
    G_out = G_sym[sel]
    F_out = F_sym[sel] if F_sym is not None else None
    return X_out, Y_out, G_out, F_out


def _upsample_time_train(X: np.ndarray, Y: np.ndarray, base_rep: int, target_min: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Repeats real/Verovio time crops and upsamples rare time classes inside a training split only."""
    if len(Y) == 0:
        return X, Y
    rng = np.random.default_rng(seed)
    idxs = [np.repeat(np.arange(len(Y)), max(1, base_rep))]
    for cid in range(len(TIME_CLASSES)):
        m = np.where(Y == cid)[0]
        have = len(m) * max(1, base_rep)
        if 0 < have < target_min:
            extra = rng.choice(m, size=min(target_min - have, len(m) * 8), replace=True)
            idxs.append(extra)
    sel = np.concatenate(idxs)
    return X[sel], Y[sel]


def _upsample_stem_dev_train(X: np.ndarray, Y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Upweights real Clean Dev stems (tail_0 2x, tail_1 3x) inside training splits only."""
    if len(Y) == 0:
        return X, Y
    idx0 = np.where(Y == 0)[0]
    idx1 = np.where(Y == 1)[0]
    idx2 = np.where(Y == 2)[0]
    parts = [np.repeat(idx0, 2), np.repeat(idx1, 3)]
    if len(idx2):
        parts.append(np.repeat(idx2, 4))
    sel = np.concatenate(parts)
    return X[sel], Y[sel]


def main() -> int:
    parser = argparse.ArgumentParser(description='Train local offline TimeNet, StemNet, and AccNet.')
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--results', required=True)
    parser.add_argument('--stem-out', default=None)
    parser.add_argument('--time-out', default=None)
    parser.add_argument('--acc-out', default=None)
    parser.add_argument('--dev-crops', default=None, help='Clean Dev 19-class crops .npz (for AccNet)')
    parser.add_argument('--verovio-time', default=None, help='5-font Verovio time crops .npz')
    parser.add_argument('--verovio-stem', default=None, help='5-font Verovio stem crops .npz')
    parser.add_argument('--verovio-sym', default=None, help='5-font Verovio 19-class crops .npz (for AccNet)')
    parser.add_argument('--cv-folds', type=int, default=5)
    parser.add_argument('--threads', type=int, default=4)
    args = parser.parse_args()

    torch.set_num_threads(args.threads)
    rng = np.random.default_rng(123)
    mpath = Path(args.manifest)
    rdir = Path(args.results)

    # ---------------- TimeNet ----------------
    if args.time_out:
        print('=== Building TimeNet v3 (10 classes, staff-row-only bridged + 5-font Verovio) ===', flush=True)
        t0 = time.time()
        tx, ty = [], []
        for cid, cname in enumerate(TIME_CLASSES):
            for _ in range(1500):
                tx.append(synthesize_time_glyph(cname, rng))
                ty.append(cid)
        X_t_syn, Y_t_syn = np.stack(tx), np.array(ty, np.int64)
        vx, vy = [], []
        for cid, cname in enumerate(TIME_CLASSES):
            for _ in range(200):
                vx.append(synthesize_time_glyph(cname, rng))
                vy.append(cid)
        X_t_val, Y_t_val = np.stack(vx), np.array(vy, np.int64)
        print(f'Synthesized {len(Y_t_syn)} train + {len(Y_t_val)} val TimeNet glyphs in {time.time() - t0:.1f}s', flush=True)

        X_t_dev, Y_t_dev, G_t_dev = extract_dev_time_crops(mpath, rdir)
        print(f'Extracted {len(Y_t_dev)} real Clean Dev time crops across {len(set(G_t_dev))} base hymns: '
              f'{ {TIME_CLASSES[k]: v for k, v in Counter(Y_t_dev.tolist()).items()} }', flush=True)

        X_t_ver = np.zeros((0, 1, TIME_SIZE, TIME_SIZE), np.uint8)
        Y_t_ver = np.zeros(0, np.int64)
        G_t_ver = np.array([], dtype=str)
        F_t_ver = np.array([], dtype=str)
        if args.verovio_time and Path(args.verovio_time).exists():
            td = np.load(args.verovio_time)
            if [str(c) for c in td['classes']] != list(TIME_CLASSES):
                sys.exit(f'TimeNet class mismatch in Verovio time crops: {list(td["classes"])} != {list(TIME_CLASSES)}')
            X_t_ver = td['X'].astype(np.uint8)
            Y_t_ver = td['Y'].astype(np.int64)
            G_t_ver = td['G'].astype(str)
            F_t_ver = td['F'].astype(str)
            print(f'Loaded {len(Y_t_ver)} Verovio 5-font time crops across {len(set(G_t_ver))} groups', flush=True)

        t_temp = 1.0
        if args.cv_folds >= 2 and (len(Y_t_dev) >= 15 or len(Y_t_ver) >= 50):
            dev_folds = make_group_folds(G_t_dev, args.cv_folds, seed=17) if len(Y_t_dev) else np.zeros(0, np.int64)
            ver_folds = make_group_folds(G_t_ver, args.cv_folds, seed=29) if len(Y_t_ver) else np.zeros(0, np.int64)
            oof_dev = np.zeros((len(Y_t_dev), len(TIME_CLASSES)), np.float32)
            oof_ver = np.zeros((len(Y_t_ver), len(TIME_CLASSES)), np.float32)
            for f in range(args.cv_folds):
                px, py = [X_t_syn], [Y_t_syn]
                d_va = np.zeros(0, np.int64)
                v_va = np.zeros(0, np.int64)
                if len(Y_t_dev):
                    d_tr = np.where(dev_folds != f)[0]
                    d_va = np.where(dev_folds == f)[0]
                    if len(d_tr):
                        dx_u, dy_u = _upsample_time_train(X_t_dev[d_tr], Y_t_dev[d_tr], 3, 220, seed=150 + f)
                        px.append(dx_u)
                        py.append(dy_u)
                if len(Y_t_ver):
                    v_tr = np.where(ver_folds != f)[0]
                    v_va = np.where(ver_folds == f)[0]
                    if len(v_tr):
                        vx_u, vy_u = _upsample_time_train(X_t_ver[v_tr], Y_t_ver[v_tr], 3, 420, seed=250 + f)
                        px.append(vx_u)
                        py.append(vy_u)
                m_f, _ = train_small(np.concatenate(px), np.concatenate(py), 1, len(TIME_CLASSES),
                                     epochs=12, seed=200 + f)
                if len(d_va):
                    oof_dev[d_va] = predict_small_logits(m_f, X_t_dev[d_va])
                if len(v_va):
                    oof_ver[v_va] = predict_small_logits(m_f, X_t_ver[v_va])
            if len(Y_t_dev):
                t_temp = fit_temperature(oof_dev, Y_t_dev)
                _report_oof(f'TimeNet Clean Dev {args.cv_folds}-Fold OOF (T={t_temp:.3f})', oof_dev, Y_t_dev, list(TIME_CLASSES))
            if len(Y_t_ver):
                _report_oof(f'TimeNet Verovio 5-Font {args.cv_folds}-Fold OOF', oof_ver, Y_t_ver, list(TIME_CLASSES), F_t_ver)

        px, py = [X_t_syn], [Y_t_syn]
        if len(Y_t_dev):
            dx_u, dy_u = _upsample_time_train(X_t_dev, Y_t_dev, 3, 250, seed=177)
            px.append(dx_u)
            py.append(dy_u)
        if len(Y_t_ver):
            vx_u, vy_u = _upsample_time_train(X_t_ver, Y_t_ver, 3, 450, seed=277)
            px.append(vx_u)
            py.append(vy_u)
        t_model, val_t_logits = train_small(np.concatenate(px), np.concatenate(py), 1, len(TIME_CLASSES),
                                            epochs=16, seed=77, X_val=X_t_val, Y_val=Y_t_val)
        assert val_t_logits is not None
        print(f'=== TimeNet Synthetic Val Accuracy: {(val_t_logits.argmax(1) == Y_t_val).mean():.4%} ===', flush=True)
        time_out = Path(args.time_out)
        export_small_npz(t_model, time_out, list(TIME_CLASSES), temperature=t_temp)
        verify_small_parity(t_model, time_out, t_temp, X_t_val, 'TimeNet v3')

    # ---------------- StemNet ----------------
    if args.stem_out:
        print('=== Building StemNet v3 (3 tail classes, Clean Dev + 5-font Verovio) ===', flush=True)
        X_s_dev, Y_s_dev, G_s_dev = extract_dev_stems(mpath, rdir)
        print(f'Extracted {len(Y_s_dev)} exact Clean Dev stem crops across {len(set(G_s_dev))} base hymns: '
              f'{dict(Counter(Y_s_dev.tolist()))}', flush=True)

        X_s_ver = np.zeros((0, 3, STEM_SIZE, STEM_SIZE), np.uint8)
        Y_s_ver = np.zeros(0, np.int64)
        G_s_ver = np.array([], dtype=str)
        F_s_ver = np.array([], dtype=str)
        if args.verovio_stem and Path(args.verovio_stem).exists():
            sd = np.load(args.verovio_stem)
            if [str(c) for c in sd['classes']] != ['tail_0', 'tail_1', 'tail_2']:
                sys.exit(f'StemNet class mismatch in Verovio stem crops: {list(sd["classes"])}')
            X_s_ver = sd['X'].astype(np.uint8)
            Y_s_ver = sd['Y'].astype(np.int64)
            G_s_ver = sd['G'].astype(str)
            F_s_ver = sd['F'].astype(str)
            print(f'Loaded {len(Y_s_ver)} Verovio 5-font stem crops: {dict(Counter(Y_s_ver.tolist()))}', flush=True)

        t0 = time.time()
        sx, sy = [], []
        for t in (0, 1, 2):
            for _ in range(1600):
                sx.append((synthesize_stem(t, rng) * 255.0).round().astype(np.uint8))
                sy.append(t)
        X_s_syn, Y_s_syn = np.stack(sx), np.array(sy, np.int64)
        print(f'Synthesized {len(Y_s_syn)} stem patches in {time.time() - t0:.1f}s', flush=True)

        s_temp = 1.0
        if args.cv_folds >= 2 and len(Y_s_dev) >= 200:
            dev_folds = make_group_folds(G_s_dev, args.cv_folds, seed=7)
            ver_folds = make_group_folds(G_s_ver, args.cv_folds, seed=31) if len(Y_s_ver) else np.zeros(0, np.int64)
            oof_dev = np.zeros((len(Y_s_dev), 3), np.float32)
            oof_ver = np.zeros((len(Y_s_ver), 3), np.float32)
            for f in range(args.cv_folds):
                d_tr = np.where(dev_folds != f)[0]
                d_va = np.where(dev_folds == f)[0]
                X_sd_tr, Y_sd_tr = _upsample_stem_dev_train(X_s_dev[d_tr], Y_s_dev[d_tr])
                px, py = [X_s_syn, X_sd_tr], [Y_s_syn, Y_sd_tr]
                v_va = np.zeros(0, np.int64)
                if len(Y_s_ver):
                    v_tr = np.where(ver_folds != f)[0]
                    v_va = np.where(ver_folds == f)[0]
                    px.append(X_s_ver[v_tr])
                    py.append(Y_s_ver[v_tr])
                X_tr, Y_tr = np.concatenate(px), np.concatenate(py)
                print(f'--- StemNet CV Fold {f + 1}/{args.cv_folds}: train={len(Y_tr)} dev_val={len(d_va)} ver_val={len(v_va)} ---', flush=True)
                m_f, vl = train_small(X_tr, Y_tr, 3, 3, epochs=14, seed=300 + f,
                                      X_val=X_s_dev[d_va], Y_val=Y_s_dev[d_va], weight_pow=0.18)
                oof_dev[d_va] = vl
                if len(v_va):
                    oof_ver[v_va] = predict_small_logits(m_f, X_s_ver[v_va])
            s_temp = fit_temperature(oof_dev, Y_s_dev)
            _report_oof(f'StemNet Clean Dev {args.cv_folds}-Fold OOF (T={s_temp:.3f})', oof_dev, Y_s_dev, ['tail_0', 'tail_1', 'tail_2'])
            if len(Y_s_ver):
                _report_oof(f'StemNet Verovio 5-Font {args.cv_folds}-Fold OOF', oof_ver, Y_s_ver, ['tail_0', 'tail_1', 'tail_2'], F_s_ver)

        px, py = [X_s_syn], [Y_s_syn]
        if len(Y_s_dev):
            X_sd_all, Y_sd_all = _upsample_stem_dev_train(X_s_dev, Y_s_dev)
            px.append(X_sd_all)
            py.append(Y_sd_all)
        if len(Y_s_ver):
            px.append(X_s_ver)
            py.append(Y_s_ver)
        s_model, _ = train_small(np.concatenate(px), np.concatenate(py), 3, 3, epochs=16, seed=88, weight_pow=0.18)
        stem_out = Path(args.stem_out)
        export_small_npz(s_model, stem_out, ['tail_0', 'tail_1', 'tail_2'], temperature=s_temp)
        verify_small_parity(s_model, stem_out, s_temp, X_s_dev if len(X_s_dev) >= 128 else X_s_syn, 'StemNet v3')

    # ---------------- AccNet v1 ----------------
    if args.acc_out:
        print('=== Building AccNet v1 (4 classes: none, sharp, flat, natural; <=100 KB) ===', flush=True)
        t0 = time.time()
        # 1. Procedural synthetic accidentals + non-accidental hard negatives.
        ax_syn, ay_syn = [], []
        for cls_name, lbl in (('acc_sharp', 1), ('acc_flat', 2), ('acc_natural', 3)):
            for _ in range(1000):
                ax_syn.append((synthesize_sample(cls_name, rng) * 255.0).round().astype(np.uint8))
                ay_syn.append(lbl)
        neg_syn_classes = ('noise', 'head_filled', 'head_hollow', 'head_whole', 'rest_quarter',
                           'rest_eighth', 'clef_G', 'clef_F', 'dynamic', 'fermata', 'dot')
        for _ in range(2200):
            cname = str(rng.choice(neg_syn_classes))
            ax_syn.append((synthesize_sample(cname, rng) * 255.0).round().astype(np.uint8))
            ay_syn.append(0)
        X_a_syn, Y_a_syn = np.stack(ax_syn), np.array(ay_syn, np.int64)
        print(f'Synthesized {len(Y_a_syn)} AccNet patches in {time.time() - t0:.1f}s', flush=True)

        # 2. Real Clean Dev accidentals + hard left-of-head negatives.
        dev_x_parts, dev_y_parts, dev_g_parts = [], [], []
        if args.dev_crops and Path(args.dev_crops).exists():
            dd = np.load(args.dev_crops)
            dx, dy, dg, _ = _build_acc_split(dd['X'].astype(np.uint8), dd['Y'].astype(np.int64),
                                             dd['G'].astype(str), None, neg_cap=3000, seed=41)
            dev_x_parts.append(dx)
            dev_y_parts.append(dy)
            dev_g_parts.append(dg)
        X_left_neg, G_left_neg = extract_dev_left_negatives(mpath, rdir, max_per_page=28)
        if len(G_left_neg):
            print(f'Extracted {len(G_left_neg)} Clean Dev hard left-of-head negatives across {len(set(G_left_neg))} base hymns', flush=True)
            dev_x_parts.append(X_left_neg)
            dev_y_parts.append(np.zeros(len(G_left_neg), dtype=np.int64))
            dev_g_parts.append(G_left_neg)
        X_a_dev = np.concatenate(dev_x_parts, axis=0) if dev_x_parts else np.zeros((0, 3, PATCH_SIZE, PATCH_SIZE), np.uint8)
        Y_a_dev = np.concatenate(dev_y_parts, axis=0) if dev_y_parts else np.zeros(0, np.int64)
        G_a_dev = np.concatenate(dev_g_parts, axis=0) if dev_g_parts else np.array([], dtype=str)
        print(f'Clean Dev AccNet total: {len(Y_a_dev)} crops {dict(Counter(Y_a_dev.tolist()))}', flush=True)

        # 3. 5-font Verovio SMuFL accidentals + non-accidental negatives.
        X_a_ver = np.zeros((0, 3, PATCH_SIZE, PATCH_SIZE), np.uint8)
        Y_a_ver = np.zeros(0, np.int64)
        G_a_ver = np.array([], dtype=str)
        F_a_ver = np.array([], dtype=str)
        if args.verovio_sym and Path(args.verovio_sym).exists():
            vd = np.load(args.verovio_sym)
            X_a_ver, Y_a_ver, G_a_ver, F_a_ver = _build_acc_split(
                vd['X'].astype(np.uint8), vd['Y'].astype(np.int64),
                vd['G'].astype(str), vd['F'].astype(str), neg_cap=4500, seed=43)
            print(f'Verovio 5-font AccNet total: {len(Y_a_ver)} crops {dict(Counter(Y_a_ver.tolist()))}', flush=True)

        # Compact channels (16, 32, 56), fc_dim=56 -> ~75 KB compressed npz (<= 100 KB).
        acc_ch = (16, 32, 56)
        acc_fc = 56
        a_temp = 1.0
        if args.cv_folds >= 2 and len(Y_a_dev) >= 200:
            dev_folds = make_group_folds(G_a_dev, args.cv_folds, seed=7)
            ver_folds = make_group_folds(G_a_ver, args.cv_folds, seed=37) if len(Y_a_ver) else np.zeros(0, np.int64)
            oof_dev = np.zeros((len(Y_a_dev), 4), np.float32)
            oof_ver = np.zeros((len(Y_a_ver), 4), np.float32)
            for f in range(args.cv_folds):
                d_tr = np.where(dev_folds != f)[0]
                d_va = np.where(dev_folds == f)[0]
                # Gently upsample rare real Clean Dev accidentals inside training fold only.
                tr_idx = [d_tr]
                frng = np.random.default_rng(600 + f)
                for cid in (1, 2, 3):
                    cm = d_tr[Y_a_dev[d_tr] == cid]
                    if 0 < len(cm) < 350:
                        tr_idx.append(frng.choice(cm, size=min(350 - len(cm), len(cm) * 6), replace=True))
                d_tr_up = np.concatenate(tr_idx)
                px, py = [X_a_syn, X_a_dev[d_tr_up]], [Y_a_syn, Y_a_dev[d_tr_up]]
                v_va = np.zeros(0, np.int64)
                if len(Y_a_ver):
                    v_tr = np.where(ver_folds != f)[0]
                    v_va = np.where(ver_folds == f)[0]
                    px.append(X_a_ver[v_tr])
                    py.append(Y_a_ver[v_tr])
                X_tr, Y_tr = np.concatenate(px), np.concatenate(py)
                print(f'--- AccNet CV Fold {f + 1}/{args.cv_folds}: train={len(Y_tr)} dev_val={len(d_va)} ver_val={len(v_va)} ---', flush=True)
                m_f, vl = train_small(X_tr, Y_tr, 3, 4, epochs=14, seed=400 + f,
                                      X_val=X_a_dev[d_va], Y_val=Y_a_dev[d_va],
                                      weight_pow=0.20, channels=acc_ch, fc_dim=acc_fc)
                oof_dev[d_va] = vl
                if len(v_va):
                    oof_ver[v_va] = predict_small_logits(m_f, X_a_ver[v_va])
            a_temp = fit_temperature(oof_dev, Y_a_dev)
            _report_oof(f'AccNet Clean Dev {args.cv_folds}-Fold OOF (T={a_temp:.3f})', oof_dev, Y_a_dev, list(ACC_CLASSES))
            if len(Y_a_ver):
                _report_oof(f'AccNet Verovio 5-Font {args.cv_folds}-Fold OOF', oof_ver, Y_a_ver, list(ACC_CLASSES), F_a_ver)

        px, py = [X_a_syn], [Y_a_syn]
        if len(Y_a_dev):
            all_idx = [np.arange(len(Y_a_dev))]
            frng = np.random.default_rng(2028)
            for cid in (1, 2, 3):
                cm = np.where(Y_a_dev == cid)[0]
                if 0 < len(cm) < 350:
                    all_idx.append(frng.choice(cm, size=min(350 - len(cm), len(cm) * 6), replace=True))
            sel = np.concatenate(all_idx)
            px.append(X_a_dev[sel])
            py.append(Y_a_dev[sel])
        if len(Y_a_ver):
            px.append(X_a_ver)
            py.append(Y_a_ver)
        a_model, _ = train_small(np.concatenate(px), np.concatenate(py), 3, 4, epochs=16, seed=99,
                                 weight_pow=0.20, channels=acc_ch, fc_dim=acc_fc)
        acc_out = Path(args.acc_out)
        size_kb = export_small_npz(a_model, acc_out, list(ACC_CLASSES), temperature=a_temp)
        if size_kb > 100.0:
            raise RuntimeError(f'AccNet exceeded 100 KB budget: {size_kb:.1f} KB')
        verify_small_parity(a_model, acc_out, a_temp, X_a_dev if len(X_a_dev) >= 128 else X_a_syn, 'AccNet v1')

    return 0


if __name__ == '__main__':
    sys.exit(main())

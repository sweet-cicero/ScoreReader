#!/usr/bin/env python3
"""Trains local offline StemNet v2 and TimeNet v2 with PyTorch CPU and exports compact NumPy weights.

Zero cloud dependency, zero holdout leakage:
1. StemNet v2 (stemnet_v2.npz):
   Classifies canonical stem-tip patches (3, 32, 32) spanning 4.5 x 4.5 staff spaces
   (down-stems flipped vertically so all stems point UP) into 3 classes:
     0: 0 tails (bare stem, slur/tie near tip, ledger lines, lyric/dynamic collision, other-voice head)
     1: 1 tail  (single eighth flag or single beam)
     2: 2 tails (double sixteenth flag, double beam, or beam + 2nd beamlet)
   Uses 6-way spatial pooling (4 quadrants + center + global max) and 5-fold base-hymn
   grouped CV on exact untied Clean Dev stems for temperature calibration.

2. TimeNet v2 (timenet_v2.npz):
   Classifies (1, 24, 24) time-signature glyph crops into 10 classes:
     '2', '3', '4', '6', '8', '9', '12', 'C', 'cut', 'other'
   Synthesizes engraved serif, bold music-style (ball-terminal 2/3/6/9, heavy 4, split C|),
   and scan-degraded digits with realistic staff-line breaks bridged ONLY on staff rows
   (never global morph-close!) matching scorereader/meter.py, plus optional Clean Dev
   5-fold base-hymn grouped CV verification and calibration.

Usage:
  $PY tools/train_stem_and_time.py --manifest out/eval/clean_dev.json \
      --results /tmp/scorereader_swarm/step3_dev \
      --stem-out /tmp/scorereader_swarm/stemnet_v2.npz \
      --time-out /tmp/scorereader_swarm/timenet_v2.npz
"""
from __future__ import annotations

import argparse
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
from scorereader.classify import _predict_small, extract_patch, load_weights, page_levels
from scorereader.layers import read_layers
from scorereader.meter import _free, bold_commons, common_signs, time_signs
from scorereader.starts import read_starts
from tools.synth_glyphs import (
    ITALIC_FONTS,
    NOTO_MUSIC,
    SERIF_FONTS,
    TIME_CLASSES,
    TIME_TO_ID,
    _degrade_scan_levels,
    _draw_font_glyph,
)
from tools.train_classifier import fit_temperature, fold_conv_bn, pool_spatial_torch

STEM_SIZE = 32
STEM_SPACES = 4.5
TIME_SIZE = 24


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
    """Compact 3-conv spatial-pooled classifier (~55K params, ~102 KB fp16 npz) for StemNet and TimeNet."""

    def __init__(self, in_ch: int, num_classes: int) -> None:
        super().__init__()
        self.c1 = nn.Conv2d(in_ch, 20, 3, padding=1, bias=True)
        self.b1 = nn.BatchNorm2d(20)
        self.c2 = nn.Conv2d(20, 40, 3, padding=1, bias=True)
        self.b2 = nn.BatchNorm2d(40)
        self.c3 = nn.Conv2d(40, 64, 3, padding=1, bias=True)
        self.b3 = nn.BatchNorm2d(64)
        self.drop = nn.Dropout(0.20)
        self.fc1 = nn.Linear(64 * 6, 64)
        self.fc2 = nn.Linear(64, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = F.max_pool2d(F.relu(self.b1(self.c1(x))), 2)
        x = F.max_pool2d(F.relu(self.b2(self.c2(x))), 2)
        x = F.relu(self.b3(self.c3(x)))
        feat = pool_spatial_torch(x)
        feat = F.relu(self.fc1(self.drop(feat)))
        return self.fc2(feat)


def export_small_npz(model: SmallConvNet, path: Path, classes: list[str], temperature: float = 1.0) -> None:
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
    print(f'Exported -> {path} ({path.stat().st_size / 1024:.1f} KB, T={temperature:.3f})', flush=True)


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
                # Simulates down-stem colliding with lyric syllables right at the tip (pascha-hypakoe failure mode).
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
                        # Dotted-eighth + sixteenth partial second beamlet.
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

        # Match ONLY exact (midi, length) pairs to prevent cross-note scrambling.
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
                direction = 'up' if note.get('voice', 1) == 1 else 'down'
                p = extract_stem_patch(grey, bare, staff['rows'], staff['space'],
                                       float(stem_info['x']), float(stem_info['end']), direction, levels=levels)
                xs.append((p * 255.0).round().astype(np.uint8))
                ys.append(lbl)
                gs.append(base_id)
    if not xs:
        return np.zeros((0, 3, STEM_SIZE, STEM_SIZE), np.uint8), np.zeros(0, np.int64), np.array([], dtype=str)
    return np.stack(xs, axis=0), np.array(ys, dtype=np.int64), np.array(gs)


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
        # Engraved music 3: open left mouth (narrow or wide) and bold round ball terminals.
        cv2.ellipse(canvas, (int(cx + 0.04 * w_px), int(y0 + 0.26 * h_px)),
                    (int(0.42 * w_px), int(0.24 * h_px)), 0, -165, 95, 0, t, cv2.LINE_AA)
        cv2.ellipse(canvas, (int(cx + 0.04 * w_px), int(y0 + 0.74 * h_px)),
                    (int(0.44 * w_px), int(0.26 * h_px)), 0, -95, 165, 0, t, cv2.LINE_AA)
        # Round ball terminals at top-left and bottom-left (including heavy Maestro/Petrucci style).
        br = max(2, int(round(h_px * rng.uniform(0.11, 0.19))))
        cv2.circle(canvas, (int(x0 + 0.18 * w_px), int(y0 + 0.23 * h_px)), br, 0, -1, cv2.LINE_AA)
        cv2.circle(canvas, (int(x0 + 0.18 * w_px), int(y0 + 0.77 * h_px)), br, 0, -1, cv2.LINE_AA)
        # Middle pinch bar pointing right.
        cv2.line(canvas, (int(cx - 0.16 * w_px), int(cy)), (int(cx + 0.24 * w_px), int(cy)), 0, max(2, int(0.95 * t)), cv2.LINE_AA)
        if rng.random() < 0.35:
            # Heavy engraved 3 where upper/lower left bulbs nearly touch across the middle staff line.
            cv2.ellipse(canvas, (int(x0 + 0.17 * w_px), int(y0 + 0.34 * h_px)), (int(0.14 * w_px), int(0.11 * h_px)), 0, 0, 360, 0, -1, cv2.LINE_AA)
            cv2.ellipse(canvas, (int(x0 + 0.17 * w_px), int(y0 + 0.66 * h_px)), (int(0.14 * w_px), int(0.11 * h_px)), 0, 0, 360, 0, -1, cv2.LINE_AA)

    elif cls_name == '4':
        # Engraved bold music 4: heavy diagonal, horizontal bar at ~66%, thick right stem, optional filled triangle.
        stem_x = int(round(cx + rng.uniform(0.08, 0.22) * w_px))
        bar_y = int(round(y0 + rng.uniform(0.58, 0.70) * h_px))
        apex_x = int(round(stem_x - rng.uniform(0.0, 0.14) * w_px))
        cv2.line(canvas, (apex_x, int(y0 + 0.04 * h_px)), (int(x0 + 0.04 * w_px), bar_y), 0, t, cv2.LINE_AA)
        cv2.line(canvas, (int(x0 + 0.02 * w_px), bar_y), (int(x1 - 0.02 * w_px), bar_y), 0, t, cv2.LINE_AA)
        cv2.line(canvas, (stem_x, int(y0 + 0.18 * h_px)), (stem_x, int(y1 - 0.04 * h_px)), 0, t, cv2.LINE_AA)
        if rng.random() < 0.45:
            # Heavy engraved foot serif.
            cv2.line(canvas, (int(stem_x - 0.22 * w_px), int(y1 - 0.04 * h_px)),
                     (int(stem_x + 0.22 * w_px), int(y1 - 0.04 * h_px)), 0, max(2, t // 2), cv2.LINE_AA)
        if rng.random() < 0.35:
            # Thick ink bleed partially fills the small interior triangle.
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
        # Solid continuous left spine + closed lower oval + top-right hook/ball.
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
                # Thicken strokes to match bold music engravings.
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

    # Simulate realistic staff lines crossing the glyph at top, middle, and bottom.
    staff_rows = [cy - space, cy, cy + space]
    with_lines = canvas.copy()
    for ry_f in staff_rows:
        ry = int(round(ry_f))
        if 0 <= ry < canvas_s:
            cv2.line(with_lines, (0, ry), (canvas_s - 1, ry), int(rng.uniform(0, 60)), line_t)

    degraded, _, (dark, paper) = _degrade_scan_levels(with_lines, rng, bare=None)
    thresh = dark + 0.55 * (paper - dark)
    ink = (degraded < thresh).astype(np.uint8)

    # Remove staff lines exactly as scorereader.layers.staff_lines does (thin horizontal pixels on staff rows).
    limit = int(round(line_t + max(2.0, 0.5 * line_t)))
    tall = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((limit + 1, 1), np.uint8))
    thin = ink & (1 - tall)
    lines_mask = np.zeros_like(ink)
    half = int(np.ceil(line_t / 2.0 + 2))
    for ry_f in staff_rows:
        ry = int(round(ry_f))
        lines_mask[max(0, ry - half):min(canvas_s, ry + half + 1), :] |= thin[max(0, ry - half):min(canvas_s, ry + half + 1), :]
    free = ink & (1 - lines_mask)

    # Bridge ONLY on staff-line rows (never global morph-close across open mouth of '3'!).
    if rng.random() < 0.85:
        free = _bridge_staff_rows_only(free, staff_rows, float(line_t))

    # Restrict crop to the glyph column span so distant noise never leaks in.
    ys_orig, xs_orig = np.nonzero(canvas < 220)
    if len(ys_orig) < 6:
        return np.zeros((1, TIME_SIZE, TIME_SIZE), dtype=np.uint8)
    gx0 = max(0, int(xs_orig.min()) - 2)
    gx1 = min(canvas_s, int(xs_orig.max()) + 3)
    gy0 = max(0, int(ys_orig.min()) - 2)
    gy1 = min(canvas_s, int(ys_orig.max()) + 3)

    if rng.random() < 0.78:
        # Binary mask mode (exact match to meter.py:_classify_digit -> classify_time_crop).
        sub = free[gy0:gy1, gx0:gx1].astype(np.float32)
    else:
        # Grayscale inverted ink mode for grayscale callers.
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
                weight_pow: float = 0.22) -> tuple[SmallConvNet, np.ndarray | None]:
    torch.manual_seed(seed)
    model = SmallConvNet(in_ch, num_classes)
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


def main() -> int:
    parser = argparse.ArgumentParser(description='Train local offline StemNet v2 and TimeNet v2.')
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--results', required=True)
    parser.add_argument('--stem-out', required=True)
    parser.add_argument('--time-out', required=True)
    parser.add_argument('--cv-folds', type=int, default=5)
    parser.add_argument('--threads', type=int, default=12)
    args = parser.parse_args()

    torch.set_num_threads(args.threads)
    rng = np.random.default_rng(123)
    mpath = Path(args.manifest)
    rdir = Path(args.results)

    # ---------------- TimeNet v2 ----------------
    print('=== Building TimeNet v2 (10 classes, staff-row-only bridged) ===', flush=True)
    t0 = time.time()
    tx, ty = [], []
    for cid, cname in enumerate(TIME_CLASSES):
        for _ in range(1800):
            tx.append(synthesize_time_glyph(cname, rng))
            ty.append(cid)
    X_t_syn, Y_t_syn = np.stack(tx), np.array(ty, np.int64)
    # Generate a held-out synthetic validation set (200/class) to measure 3 vs 6 and C vs cut cleanly.
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

    # 5-fold base-hymn grouped CV on Clean Dev time crops (augmented lightly with synthetic).
    t_temp = 1.0
    if len(Y_t_dev) >= 15 and len(set(G_t_dev)) >= 5:
        uniq = sorted(set(G_t_dev))
        grng = np.random.default_rng(17)
        grng.shuffle(uniq)
        fmap = {g: i % args.cv_folds for i, g in enumerate(uniq)}
        folds = np.array([fmap[g] for g in G_t_dev])
        oof_t = np.zeros((len(Y_t_dev), len(TIME_CLASSES)), np.float32)
        for f in range(args.cv_folds):
            tr = np.where(folds != f)[0]
            va = np.where(folds == f)[0]
            if len(va) == 0:
                continue
            # Lightly repeat real training crops x3 so real engravings influence weights without overwhelming synthetic.
            X_tr = np.concatenate([X_t_syn, np.repeat(X_t_dev[tr], 3, axis=0)], axis=0)
            Y_tr = np.concatenate([Y_t_syn, np.repeat(Y_t_dev[tr], 3, axis=0)], axis=0)
            _, vl = train_small(X_tr, Y_tr, 1, len(TIME_CLASSES), epochs=12, seed=200 + f,
                                X_val=X_t_dev[va], Y_val=Y_t_dev[va])
            oof_t[va] = vl
        t_oof_acc = float((oof_t.argmax(1) == Y_t_dev).mean())
        t_temp = fit_temperature(oof_t, Y_t_dev)
        print(f'=== TimeNet Clean Dev {args.cv_folds}-Fold OOF Accuracy: {t_oof_acc:.4%} (T={t_temp:.3f}) ===', flush=True)
        for cid in sorted(set(Y_t_dev)):
            m = Y_t_dev == cid
            print(f'  {TIME_CLASSES[cid]:8s}: {(oof_t[m].argmax(1) == cid).mean():7.2%} ({int(m.sum())} crops)', flush=True)

    X_t_all = np.concatenate([X_t_syn, np.repeat(X_t_dev, 3, axis=0)], axis=0) if len(Y_t_dev) else X_t_syn
    Y_t_all = np.concatenate([Y_t_syn, np.repeat(Y_t_dev, 3, axis=0)], axis=0) if len(Y_t_dev) else Y_t_syn
    t_model, val_t_logits = train_small(X_t_all, Y_t_all, 1, len(TIME_CLASSES), epochs=16, seed=77,
                                        X_val=X_t_val, Y_val=Y_t_val)
    assert val_t_logits is not None
    print(f'=== TimeNet Synthetic Val Accuracy: {(val_t_logits.argmax(1) == Y_t_val).mean():.4%} ===', flush=True)
    for cid in range(len(TIME_CLASSES)):
        m = Y_t_val == cid
        print(f'  syn {TIME_CLASSES[cid]:6s}: {(val_t_logits[m].argmax(1) == cid).mean():7.2%}', flush=True)
    time_out = Path(args.time_out)
    export_small_npz(t_model, time_out, list(TIME_CLASSES), temperature=t_temp)
    verify_small_parity(t_model, time_out, t_temp, X_t_val, 'TimeNet v2')

    # ---------------- StemNet v2 ----------------
    print('=== Building StemNet v2 (3 tail classes, 5-fold grouped CV) ===', flush=True)
    X_s_dev, Y_s_dev, G_s_dev = extract_dev_stems(mpath, rdir)
    print(f'Extracted {len(Y_s_dev)} exact Clean Dev stem crops across {len(set(G_s_dev))} base hymns: '
          f'{dict(Counter(Y_s_dev.tolist()))}', flush=True)

    t0 = time.time()
    sx, sy = [], []
    for t in (0, 1, 2):
        n_syn = 2000 if t in (0, 1) else 2200
        for _ in range(n_syn):
            sx.append((synthesize_stem(t, rng) * 255.0).round().astype(np.uint8))
            sy.append(t)
    X_s_syn, Y_s_syn = np.stack(sx), np.array(sy, np.int64)
    print(f'Synthesized {len(Y_s_syn)} stem patches in {time.time() - t0:.1f}s', flush=True)

    s_temp = 1.0
    if args.cv_folds >= 2 and len(Y_s_dev) >= 200:
        uniq = sorted(set(G_s_dev))
        srng = np.random.default_rng(7)
        srng.shuffle(uniq)
        fmap = {g: i % args.cv_folds for i, g in enumerate(uniq)}
        folds = np.array([fmap[g] for g in G_s_dev])
        oof_s = np.zeros((len(Y_s_dev), 3), np.float32)
        for f in range(args.cv_folds):
            tr = np.where(folds != f)[0]
            va = np.where(folds == f)[0]
            print(f'--- StemNet CV Fold {f + 1}/{args.cv_folds}: real_train={len(tr)} real_val={len(va)} ---', flush=True)
            X_tr = np.concatenate([X_s_syn, X_s_dev[tr]], axis=0)
            Y_tr = np.concatenate([Y_s_syn, Y_s_dev[tr]], axis=0)
            _, vl = train_small(X_tr, Y_tr, 3, 3, epochs=16, seed=300 + f,
                                X_val=X_s_dev[va], Y_val=Y_s_dev[va], weight_pow=0.20)
            oof_s[va] = vl
        s_preds = oof_s.argmax(1)
        s_oof_acc = float((s_preds == Y_s_dev).mean())
        s_temp = fit_temperature(oof_s, Y_s_dev)
        print(f'=== StemNet Clean Dev {args.cv_folds}-Fold OOF Accuracy: {s_oof_acc:.4%} (calibrated T={s_temp:.3f}) ===', flush=True)
        for cid, cname in enumerate(('tail_0', 'tail_1', 'tail_2')):
            m = Y_s_dev == cid
            if m.any():
                p = s_preds == cid
                tp = int((m & p).sum())
                rec = tp / int(m.sum())
                prec = tp / max(1, int(p.sum()))
                print(f'  {cname:8s}: rec={rec:7.2%} prec={prec:7.2%} ({int(m.sum()):5d} crops)', flush=True)

    X_s_all = np.concatenate([X_s_syn, X_s_dev], axis=0) if len(Y_s_dev) else X_s_syn
    Y_s_all = np.concatenate([Y_s_syn, Y_s_dev], axis=0) if len(Y_s_dev) else Y_s_syn
    s_model, _ = train_small(X_s_all, Y_s_all, 3, 3, epochs=18, seed=88, weight_pow=0.20)
    stem_out = Path(args.stem_out)
    export_small_npz(s_model, stem_out, ['tail_0', 'tail_1', 'tail_2'], temperature=s_temp)
    verify_small_parity(s_model, stem_out, s_temp, X_s_dev if len(X_s_dev) >= 128 else X_s_syn, 'StemNet v2')
    return 0


if __name__ == '__main__':
    sys.exit(main())

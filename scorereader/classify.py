"""Local offline neural symbol classifier (SymNet) running in pure NumPy + OpenCV.

Zero cloud models, zero internet dependency, zero PyTorch runtime dependency.
Loads compact folded-BatchNorm weights from `symnet.npz` (trained offline on synthetic
multi-font music engravings plus Clean Dev crops only, never holdout pages).

Classes (19):
  0: head_filled   1: head_hollow   2: head_whole    3: head_breve
  4: rest_whole    5: rest_half     6: rest_quarter  7: rest_eighth   8: rest_16th
  9: acc_sharp    10: acc_flat     11: acc_natural
 12: clef_G       13: clef_F       14: clef_C
 15: dot          16: dynamic      17: fermata      18: noise
"""
from __future__ import annotations

import os
from pathlib import Path

import cv2
import numpy as np

from . import setting

PATCH_SIZE = 32
PATCH_SPACES = 3.5

CLASSES = (
    'head_filled', 'head_hollow', 'head_whole', 'head_breve',
    'rest_whole', 'rest_half', 'rest_quarter', 'rest_eighth', 'rest_16th',
    'acc_sharp', 'acc_flat', 'acc_natural',
    'clef_G', 'clef_F', 'clef_C',
    'dot', 'dynamic', 'fermata', 'noise',
)
CLASS_TO_ID = {name: idx for idx, name in enumerate(CLASSES)}

HEAD_IDS = (0, 1, 2, 3)
REST_IDS = (4, 5, 6, 7, 8)
ACC_IDS = (9, 10, 11)
NON_HEAD_IDS = (4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18)

ACC_CLASSES = ('none', 'sharp', 'flat', 'natural')

WEIGHTS = str(Path(__file__).resolve().parent / 'symnet.npz')
STEM_WEIGHTS = str(Path(__file__).resolve().parent / 'stemnet.npz')
TIME_WEIGHTS = str(Path(__file__).resolve().parent / 'timenet.npz')
ACC_WEIGHTS = str(Path(__file__).resolve().parent / 'accnet.npz')
OFF = ('off', 'none', 'no', '0', '')
_CACHE: dict[str, dict] = {}


def weights_path(env_key: str = 'SYMNET', default: str = WEIGHTS) -> str | None:
    """Returns a local neural weights path, or None when disabled via SCOREREADER_<KEY>=off."""
    named = setting(env_key)
    if named is not None:
        return None if named.strip().lower() in OFF else named
    return default if os.path.exists(default) else None


def load_weights(path: str | None = None, env_key: str = 'SYMNET', default: str = WEIGHTS) -> dict | None:
    """Loads folded weights once into float32 arrays."""
    path = path or weights_path(env_key, default)
    if not path or not os.path.exists(path):
        return None
    if path not in _CACHE:
        with np.load(path) as data:
            loaded = {}
            for key in data.files:
                if key == 'classes':
                    loaded[key] = tuple(str(x) for x in data[key])
                else:
                    loaded[key] = data[key].astype(np.float32)
            _CACHE[path] = loaded
    return _CACHE[path]


def load_stem_weights(path: str | None = None) -> dict | None:
    """Loads folded StemNet weights once."""
    return load_weights(path, env_key='STEMNET', default=STEM_WEIGHTS)


def load_time_weights(path: str | None = None) -> dict | None:
    """Loads folded TimeNet weights once."""
    return load_weights(path, env_key='TIMENET', default=TIME_WEIGHTS)


def load_acc_weights(path: str | None = None) -> dict | None:
    """Loads folded AccNet weights once."""
    return load_weights(path, env_key='ACCNET', default=ACC_WEIGHTS)


def page_levels(grey: np.ndarray) -> tuple[float, float]:
    """Computes robust (dark, paper) grayscale intensity percentiles once per page."""
    paper = float(np.percentile(grey[::9, ::9], 85)) if grey.size > 100 else 255.0
    dark_px = grey[grey < paper - 20]
    dark = float(np.percentile(dark_px[::7], 20)) if dark_px.size > 20 else 20.0
    return dark, paper


def extract_patch(grey: np.ndarray, bare: np.ndarray, staff_rows: list[float], space: float,
                  cx: float, cy: float, size: int = PATCH_SIZE, spaces: float = PATCH_SPACES,
                  levels: tuple[float, float] | None = None) -> np.ndarray:
    """Extracts a normalized 3-channel (3, size, size) float32 patch centered at (cx, cy).

    Channel 0: inverted normalized grayscale ink in [0, 1].
    Channel 1: staff-line-removed bare ink in [0, 1].
    Channel 2: staff-line geometry mask in [0, 1].
    """
    half = int(round(0.5 * spaces * space))
    side = 2 * half + 1
    h, w = grey.shape
    x0, y0 = int(round(cx)) - half, int(round(cy)) - half
    x1, y1 = x0 + side, y0 + side

    dark, paper = page_levels(grey) if levels is None else levels
    denom = max(25.0, paper - dark)

    g_crop = np.full((side, side), paper, dtype=np.float32)
    b_crop = np.zeros((side, side), dtype=np.float32)
    l_crop = np.zeros((side, side), dtype=np.float32)

    sx0, sy0 = max(0, x0), max(0, y0)
    sx1, sy1 = min(w, x1), min(h, y1)
    if sx1 > sx0 and sy1 > sy0:
        dx0, dy0 = sx0 - x0, sy0 - y0
        dx1, dy1 = dx0 + (sx1 - sx0), dy0 + (sy1 - sy0)
        g_crop[dy0:dy1, dx0:dx1] = grey[sy0:sy1, sx0:sx1]
        b_crop[dy0:dy1, dx0:dx1] = (bare[sy0:sy1, sx0:sx1] > 0).astype(np.float32)

    for row in staff_rows:
        ry = int(round(row - y0))
        if 0 <= ry < side:
            r0, r1 = max(0, ry - 1), min(side, ry + 2)
            l_crop[r0:r1, :] = 1.0

    ch0 = np.clip((paper - g_crop) / denom, 0.0, 1.0)
    interp = cv2.INTER_AREA if side > size else cv2.INTER_LINEAR
    p0 = cv2.resize(ch0, (size, size), interpolation=interp)
    p1 = cv2.resize(b_crop, (size, size), interpolation=interp)
    p2 = cv2.resize(l_crop, (size, size), interpolation=cv2.INTER_AREA)
    return np.stack([p0, p1, p2], axis=0).astype(np.float32)


def _conv3x3_relu(x: np.ndarray, weight: np.ndarray, bias: np.ndarray) -> np.ndarray:
    """Fast im2col + BLAS 3x3 same-padded convolution followed by ReLU."""
    n, c, h, w = x.shape
    padded = np.pad(x, ((0, 0), (0, 0), (1, 1), (1, 1)))
    # Build (N, C, 9, H, W) view using explicit slice stacking (fast and contiguous for BLAS matmul).
    cols = np.empty((n, c * 9, h * w), dtype=np.float32)
    idx = 0
    for ch in range(c):
        for dy in range(3):
            for dx in range(3):
                cols[:, idx, :] = padded[:, ch, dy:dy + h, dx:dx + w].reshape(n, h * w)
                idx += 1
    w_mat = weight.reshape(weight.shape[0], -1)   # (O, C*9)
    # Batched GEMM via tensordot/matmul: (O, K) @ (N, K, P) -> (N, O, P)
    out = np.matmul(w_mat[None, :, :], cols) + bias[None, :, None]
    np.maximum(out, 0.0, out=out)
    return out.reshape(n, weight.shape[0], h, w)


def _maxpool2x2(x: np.ndarray) -> np.ndarray:
    n, c, h, w = x.shape
    return x.reshape(n, c, h // 2, 2, w // 2, 2).max(axis=(3, 5))


def _pool_features(x: np.ndarray, expected_dim: int) -> np.ndarray:
    """Pools spatial features from a 4D feature map (N, C, H, W) to match fc1 input size."""
    c, h, w = x.shape[1], x.shape[2], x.shape[3]
    gmp = x.max(axis=(2, 3))
    if expected_dim == 6 * c:
        h2, w2 = h // 2, w // 2
        c0 = (h + 2) // 4
        c1 = h - c0
        w0 = (w + 2) // 4
        w1 = w - w0
        tl = x[:, :, :h2, :w2].mean(axis=(2, 3))
        tr = x[:, :, :h2, w2:].mean(axis=(2, 3))
        bl = x[:, :, h2:, :w2].mean(axis=(2, 3))
        br = x[:, :, h2:, w2:].mean(axis=(2, 3))
        ctr = x[:, :, c0:c1, w0:w1].mean(axis=(2, 3))
        return np.concatenate([tl, tr, bl, br, ctr, gmp], axis=1)
    gap = x.mean(axis=(2, 3))
    return np.concatenate([gap, gmp], axis=1)


def predict_patches(patches: np.ndarray, weights: dict) -> np.ndarray:
    """Runs SymNet forward pass on (N, 3, 32, 32) float32 patches, returning calibrated probabilities (N, 19)."""
    if len(patches) == 0:
        return np.zeros((0, len(CLASSES)), dtype=np.float32)
    x = patches.astype(np.float32, copy=False)
    x = _maxpool2x2(_conv3x3_relu(x, weights['c1w'], weights['c1b']))   # 16x16
    x = _maxpool2x2(_conv3x3_relu(x, weights['c2w'], weights['c2b']))   # 8x8
    x = _maxpool2x2(_conv3x3_relu(x, weights['c3w'], weights['c3b']))   # 4x4
    x = _conv3x3_relu(x, weights['c4w'], weights['c4b'])                # 4x4
    feat = _pool_features(x, int(weights['fc1w'].shape[0]))
    feat = np.maximum(feat @ weights['fc1w'] + weights['fc1b'], 0.0)
    logits = feat @ weights['fc2w'] + weights['fc2b']
    temp = float(weights['temperature'][0]) if 'temperature' in weights else 1.0
    logits = logits / max(0.1, temp)
    logits -= logits.max(axis=1, keepdims=True)
    probs = np.exp(logits)
    probs /= probs.sum(axis=1, keepdims=True)
    return probs.astype(np.float32)


def classify_points(layers: dict, points: list[tuple[int, float, float]],
                    weights: dict | None = None) -> np.ndarray:
    """Extracts patches and classifies a list of (staff_index, cx, cy) points on a page."""
    weights = weights or load_weights()
    if weights is None or not points:
        return np.zeros((0, len(CLASSES)), dtype=np.float32)
    grey = layers['grey']
    bare = layers['bare']
    staves = layers['staves']
    levels = page_levels(grey)
    batch = np.empty((len(points), 3, PATCH_SIZE, PATCH_SIZE), dtype=np.float32)
    for i, (s_idx, cx, cy) in enumerate(points):
        staff = staves[s_idx]
        batch[i] = extract_patch(grey, bare, staff['rows'], staff['space'], cx, cy, levels=levels)
    return predict_patches(batch, weights)


def _predict_small(x: np.ndarray, weights: dict) -> np.ndarray:
    """Runs 3-conv SmallConvNet (StemNet or TimeNet) forward pass in pure NumPy."""
    if len(x) == 0:
        return np.zeros((0, len(weights['classes'])), dtype=np.float32)
    x = x.astype(np.float32, copy=False)
    x = _maxpool2x2(_conv3x3_relu(x, weights['c1w'], weights['c1b']))
    x = _maxpool2x2(_conv3x3_relu(x, weights['c2w'], weights['c2b']))
    x = _conv3x3_relu(x, weights['c3w'], weights['c3b'])
    feat = _pool_features(x, int(weights['fc1w'].shape[0]))
    feat = np.maximum(feat @ weights['fc1w'] + weights['fc1b'], 0.0)
    logits = feat @ weights['fc2w'] + weights['fc2b']
    temp = float(weights['temperature'][0]) if 'temperature' in weights else 1.0
    logits = logits / max(0.1, temp)
    logits -= logits.max(axis=1, keepdims=True)
    probs = np.exp(logits)
    probs /= probs.sum(axis=1, keepdims=True)
    return probs.astype(np.float32)


def classify_stems(layers: dict, stems: list[tuple[int, float, float, str]],
                   weights: dict | None = None) -> np.ndarray:
    """Classifies canonical stem-tip patches (staff_idx, stem_x, stem_end, direction) -> (N, 3) probs for 0/1/2 tails."""
    weights = weights or load_stem_weights()
    if weights is None or not stems:
        return np.zeros((0, 3), dtype=np.float32)
    grey = layers['grey']
    bare = layers['bare']
    staves = layers['staves']
    levels = page_levels(grey)
    batch = np.empty((len(stems), 3, PATCH_SIZE, PATCH_SIZE), dtype=np.float32)
    for i, (s_idx, sx, send, direction) in enumerate(stems):
        staff = staves[s_idx]
        p = extract_patch(grey, bare, staff['rows'], staff['space'], sx, send,
                          size=PATCH_SIZE, spaces=4.5, levels=levels)
        if direction == 'down':
            p = p[:, ::-1, :]
        batch[i] = p
    return _predict_small(batch, weights)


def classify_time_crop(mask_or_ink: np.ndarray, weights: dict | None = None) -> tuple[str | None, float]:
    """Classifies a single tight-cropped 2D ink mask/grayscale patch with TimeNet -> (label, prob)."""
    weights = weights or load_time_weights()
    if weights is None or mask_or_ink.size == 0:
        return None, 0.0
    ys, xs = np.nonzero(mask_or_ink > 0.15)
    if len(ys) < 6:
        return None, 0.0
    crop = mask_or_ink[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(np.float32)
    if crop.max() > 1.0:
        crop = crop / 255.0
    size = 24
    h, w = crop.shape
    scale = (size - 4) / max(h, w)
    nh, nw = max(1, int(round(h * scale))), max(1, int(round(w * scale)))
    resized = cv2.resize(crop, (nw, nh), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)
    out = np.zeros((1, 1, size, size), dtype=np.float32)
    y0, x0 = (size - nh) // 2, (size - nw) // 2
    out[0, 0, y0:y0 + nh, x0:x0 + nw] = resized
    probs = _predict_small(out, weights)[0]
    best = int(np.argmax(probs))
    return str(weights['classes'][best]), float(probs[best])


def classify_accidentals(layers: dict, candidates: list[tuple[int, float, float]],
                         weights: dict | None = None) -> np.ndarray:
    """Classifies left-of-head candidate points (staff_idx, cx, cy) into (N, 4) probs for (none, sharp, flat, natural)."""
    weights = weights or load_acc_weights()
    if weights is None or not candidates:
        return np.zeros((0, len(ACC_CLASSES)), dtype=np.float32)
    grey = layers['grey']
    bare = layers['bare']
    staves = layers['staves']
    levels = page_levels(grey)
    batch = np.empty((len(candidates), 3, PATCH_SIZE, PATCH_SIZE), dtype=np.float32)
    for i, (s_idx, cx, cy) in enumerate(candidates):
        staff = staves[s_idx]
        batch[i] = extract_patch(grey, bare, staff['rows'], staff['space'], cx, cy,
                                 size=PATCH_SIZE, spaces=PATCH_SPACES, levels=levels)
    return _predict_small(batch, weights)

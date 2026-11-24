"""A second look at each read head by a small trained network: is the head filled, hollow, or no head at all?

The network is a small convolutional classifier (three 3x3 layers of 16, 32 and 64 channels, each with a 2x2 max
pool, and two dense layers). It sees a square of four staff spaces around the head, scaled to 32 by 32 pixels, with
the ink high. It was trained offline on the heads that the reader read on LitChoir's scans, each labelled by the
typed hymn; its weights are a NumPy file outside the package (`SCOREREADER_HEADNET`), and without them this step is
off. Only NumPy and OpenCV run it: no model library is needed to read a page."""
from __future__ import annotations

import cv2
import numpy as np

SIZE, SPAN, PAD = 32, 4.0, 200      # the square: 32 pixels, four staff spaces; the paper set around the page

_WEIGHTS: dict[str, dict] = {}


def load(path: str) -> dict:
    """The weights of the network, read once."""
    if path not in _WEIGHTS:
        with np.load(path) as found:
            _WEIGHTS[path] = {name: found[name].astype(np.float32) for name in found.files}
    return _WEIGHTS[path]


def crops(grey: np.ndarray, heads: list[dict], space: float) -> np.ndarray:
    """The square around each head, as the network was trained on it (N, 1, 32, 32), ink high, from 0 to 1."""
    ink = cv2.copyMakeBorder(255 - grey, PAD, PAD, PAD, PAD, cv2.BORDER_CONSTANT, value=0)
    half = SPAN * space / 2
    scale = SIZE / (2 * half)
    out = np.zeros((len(heads), 1, SIZE, SIZE), np.float32)
    for index, head in enumerate(heads):
        x, y = head['cx'] + PAD, head['cy'] + PAD
        matrix = np.float32([[scale, 0, SIZE / 2 - x * scale], [0, scale, SIZE / 2 - y * scale]])
        out[index, 0] = cv2.warpAffine(ink, matrix, (SIZE, SIZE), flags=cv2.INTER_AREA) / 255.0
    return out


def _conv(x: np.ndarray, weight: np.ndarray, bias: np.ndarray) -> np.ndarray:
    """A 3x3 convolution with paper around the edge (as SAME), then max(0, .)."""
    n, c, h, w = x.shape
    padded = np.pad(x, ((0, 0), (0, 0), (1, 1), (1, 1)))
    cols = np.stack([padded[:, :, dy:dy + h, dx:dx + w] for dy in range(3) for dx in range(3)], axis=2)
    cols = cols.reshape(n, c * 9, h * w)
    out = np.einsum('ok,nkp->nop', weight.reshape(weight.shape[0], -1), cols, optimize=True)
    return np.maximum(out.reshape(n, -1, h, w) + bias[None, :, None, None], 0)


def _pool(x: np.ndarray) -> np.ndarray:
    n, c, h, w = x.shape
    return x.reshape(n, c, h // 2, 2, w // 2, 2).max(axis=(3, 5))


def kinds(grey: np.ndarray, heads: list[dict], space: float, weights: dict) -> np.ndarray:
    """For each head, how sure the network is that it is a filled head, a hollow head and no head (N, 3)."""
    if not heads:
        return np.zeros((0, 3), np.float32)
    x = crops(grey, heads, space)
    for name in ('c1', 'c2', 'c3'):
        x = _pool(_conv(x, weights[name], weights[name + 'b']))
    x = np.maximum(x.reshape(len(heads), -1) @ weights['d1'] + weights['d1b'], 0)
    logits = x @ weights['d2'] + weights['d2b']
    logits -= logits.max(axis=1, keepdims=True)
    sure = np.exp(logits)
    return sure / sure.sum(axis=1, keepdims=True)

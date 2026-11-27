#!/usr/bin/env python3
"""Trains the local offline neural symbol classifier (SymNet v2) with PyTorch CPU and exports compact NumPy weights.

Zero cloud dependency, zero holdout leakage:
  - Trains on upgraded multi-style synthetic 19-class music symbols (tools/synth_glyphs.py)
    combined with verified real Clean Dev crops (strictly clean_dev.json, never holdout).
  - Uses 6-way spatial pyramid pooling (4 quadrants + center + global max) so SymNet distinguishes
    centered heads/rests from neighboring chords, hanging vs sitting rests, and off-center noise.
  - Folds BatchNorm2d mathematically into Conv2d weights at export for 100% pure NumPy + OpenCV
    inference in scorereader/classify.py with zero PyTorch runtime dependency.
  - Runs 5-fold base-hymn grouped CV on Clean Dev crops to report honest out-of-hymn metrics per
    class and calibrate scalar temperature T before exporting final weights.

Usage:
  $PY tools/train_classifier.py --dev-crops /tmp/scorereader_swarm/dev_crops_v2.npz \
      --out /tmp/scorereader_swarm/symnet_v2.npz --synth-per-class 2000 --epochs 20
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scorereader.classify import load_weights, predict_patches
from tools.synth_glyphs import CLASSES, PATCH_SIZE, synthesize_sample


def pool_spatial_torch(x: torch.Tensor) -> torch.Tensor:
    """Pools 6 spatial descriptors (4 quadrants + center + global max) matching scorereader.classify."""
    h, w = x.shape[2], x.shape[3]
    h2, w2 = h // 2, w // 2
    c0, c1 = (h + 2) // 4, h - (h + 2) // 4
    w0, w1 = (w + 2) // 4, w - (w + 2) // 4
    tl = x[:, :, :h2, :w2].mean(dim=(2, 3))
    tr = x[:, :, :h2, w2:].mean(dim=(2, 3))
    bl = x[:, :, h2:, :w2].mean(dim=(2, 3))
    br = x[:, :, h2:, w2:].mean(dim=(2, 3))
    ctr = x[:, :, c0:c1, w0:w1].mean(dim=(2, 3))
    gmp = x.amax(dim=(2, 3))
    return torch.cat([tl, tr, bl, br, ctr, gmp], dim=1)


class SymNet(nn.Module):
    """Compact 4-conv spatial-pooled classifier (~151K params, ~275 KB fp16 npz) for 3x32x32 symbol patches."""

    def __init__(self, num_classes: int = len(CLASSES)) -> None:
        super().__init__()
        self.c1 = nn.Conv2d(3, 24, 3, padding=1, bias=True)
        self.b1 = nn.BatchNorm2d(24)
        self.c2 = nn.Conv2d(24, 48, 3, padding=1, bias=True)
        self.b2 = nn.BatchNorm2d(48)
        self.c3 = nn.Conv2d(48, 64, 3, padding=1, bias=True)
        self.b3 = nn.BatchNorm2d(64)
        self.c4 = nn.Conv2d(64, 96, 3, padding=1, bias=True)
        self.b4 = nn.BatchNorm2d(96)
        self.drop = nn.Dropout(0.22)
        self.fc1 = nn.Linear(96 * 6, 96)
        self.fc2 = nn.Linear(96, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = F.max_pool2d(F.relu(self.b1(self.c1(x))), 2)   # 16x16
        x = F.max_pool2d(F.relu(self.b2(self.c2(x))), 2)   # 8x8
        x = F.max_pool2d(F.relu(self.b3(self.c3(x))), 2)   # 4x4
        x = F.relu(self.b4(self.c4(x)))                    # 4x4
        feat = pool_spatial_torch(x)
        feat = F.relu(self.fc1(self.drop(feat)))
        return self.fc2(feat)


def fold_conv_bn(conv: nn.Conv2d, bn: nn.BatchNorm2d) -> tuple[np.ndarray, np.ndarray]:
    """Mathematically folds BatchNorm2d into Conv2d weights and bias for zero-overhead NumPy inference."""
    w = conv.weight.detach().cpu().numpy().astype(np.float64)
    b = conv.bias.detach().cpu().numpy().astype(np.float64)
    gamma = bn.weight.detach().cpu().numpy().astype(np.float64)
    beta = bn.bias.detach().cpu().numpy().astype(np.float64)
    mean = bn.running_mean.detach().cpu().numpy().astype(np.float64)
    var = bn.running_var.detach().cpu().numpy().astype(np.float64)
    scale = gamma / np.sqrt(var + bn.eps)
    w_folded = w * scale[:, None, None, None]
    b_folded = beta + (b - mean) * scale
    return w_folded.astype(np.float32), b_folded.astype(np.float32)


def export_npz(model: SymNet, path: Path, temperature: float = 1.0) -> None:
    """Exports folded weights as float16 arrays (loaded as float32 at runtime) plus class metadata."""
    model.eval()
    arrays: dict[str, np.ndarray] = {
        'classes': np.array(CLASSES),
        'temperature': np.array([temperature], dtype=np.float32),
    }
    for idx, (conv, bn) in enumerate(((model.c1, model.b1), (model.c2, model.b2),
                                      (model.c3, model.b3), (model.c4, model.b4)), 1):
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
    print(f'Exported SymNet -> {path} ({size_kb:.1f} KB, T={temperature:.3f})', flush=True)


def verify_numpy_parity(model: SymNet, npz_path: Path, temperature: float, sample_x: np.ndarray) -> float:
    """Verifies pure-NumPy inference matches PyTorch folded probabilities within float16 precision."""
    model.eval()
    x_f32 = sample_x[:128].astype(np.float32) / 255.0
    with torch.no_grad():
        logits = model(torch.from_numpy(x_f32)) / max(0.1, float(temperature))
        pt_probs = F.softmax(logits, dim=1).numpy()
    weights = load_weights(str(npz_path))
    assert weights is not None
    np_probs = predict_patches(x_f32, weights)
    max_diff = float(np.max(np.abs(pt_probs - np_probs)))
    print(f'SymNet pure-NumPy parity check (N={len(x_f32)}): max_abs_diff={max_diff:.6f}', flush=True)
    if max_diff > 5e-3:
        raise RuntimeError(f'SymNet NumPy parity error too large: {max_diff:.6f}')
    return max_diff


def augment_batch(x: torch.Tensor) -> torch.Tensor:
    """Applies zero-padded random shift (+/- 2 px) and contrast/noise jitter without edge wrap."""
    n, c, h, w = x.shape
    padded = F.pad(x, (2, 2, 2, 2), mode='constant', value=0.0)
    out = torch.empty_like(x)
    shifts_y = torch.randint(0, 5, (n,))
    shifts_x = torch.randint(0, 5, (n,))
    for i in range(n):
        sy, sx = int(shifts_y[i]), int(shifts_x[i])
        out[i] = padded[i, :, sy:sy + h, sx:sx + w]
    gain = torch.empty((n, 1, 1), dtype=x.dtype).uniform_(0.78, 1.22)
    bias = torch.empty((n, 1, 1), dtype=x.dtype).uniform_(-0.04, 0.04)
    noise = torch.randn((n, h, w), dtype=x.dtype) * 0.02
    out[:, 0] = torch.clamp(out[:, 0] * gain + bias + noise, 0.0, 1.0)
    return out


def generate_synthetic(per_class: int, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    """Generates a balanced synthetic 19-class dataset."""
    rng = np.random.default_rng(seed)
    t0 = time.time()
    xs = np.empty((per_class * len(CLASSES), 3, PATCH_SIZE, PATCH_SIZE), dtype=np.uint8)
    ys = np.empty(per_class * len(CLASSES), dtype=np.int64)
    pos = 0
    for cid, cls_name in enumerate(CLASSES):
        for _ in range(per_class):
            p = synthesize_sample(cls_name, rng)
            xs[pos] = (p * 255.0).round().astype(np.uint8)
            ys[pos] = cid
            pos += 1
    print(f'Synthesized {len(ys)} patches ({per_class}/class x {len(CLASSES)}) in {time.time() - t0:.1f}s', flush=True)
    return xs, ys


def upsample_real_train(X_real: np.ndarray, Y_real: np.ndarray, target_min: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Upsamples rare real Clean Dev classes inside a training fold only (never touches validation)."""
    if len(Y_real) == 0:
        return X_real, Y_real
    rng = np.random.default_rng(seed)
    idxs = [np.arange(len(Y_real))]
    for cid in range(len(CLASSES)):
        m = np.where(Y_real == cid)[0]
        if 0 < len(m) < target_min:
            extra = rng.choice(m, size=min(target_min - len(m), len(m) * 8), replace=True)
            idxs.append(extra)
    chosen = np.concatenate(idxs)
    return X_real[chosen], Y_real[chosen]


def fit_model(X_train: np.ndarray, Y_train: np.ndarray, epochs: int, batch_size: int, seed: int,
              X_val: np.ndarray | None = None, Y_val: np.ndarray | None = None) -> tuple[SymNet, np.ndarray | None]:
    torch.manual_seed(seed)
    model = SymNet(len(CLASSES))
    counts = np.bincount(Y_train, minlength=len(CLASSES)).astype(np.float32)
    weights = np.where(counts > 0, (counts.max() / np.maximum(counts, 1.0)) ** 0.30, 1.0)
    weights = torch.tensor(weights / weights.mean(), dtype=torch.float32)
    criterion = nn.CrossEntropyLoss(weight=weights, label_smoothing=0.02)
    opt = torch.optim.AdamW(model.parameters(), lr=2.5e-3, weight_decay=3e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)

    ds = TensorDataset(torch.from_numpy(X_train), torch.from_numpy(Y_train.astype(np.int64)))
    loader = DataLoader(ds, batch_size=batch_size, shuffle=True, drop_last=False)

    for ep in range(epochs):
        t0 = time.time()
        model.train()
        tot_loss, n_batches = 0.0, 0
        for bx, by in loader:
            bx = augment_batch(bx.float() / 255.0)
            opt.zero_grad(set_to_none=True)
            logits = model(bx)
            loss = criterion(logits, by)
            loss.backward()
            opt.step()
            tot_loss += float(loss.item())
            n_batches += 1
        sched.step()
        if (ep + 1) % 3 == 0 or ep + 1 == epochs:
            msg = f'  epoch {ep + 1:2d}/{epochs} loss={tot_loss / max(1, n_batches):.4f} ({time.time() - t0:.1f}s)'
            if X_val is not None and len(X_val):
                val_logits = predict_logits(model, X_val)
                acc = float((val_logits.argmax(1) == Y_val).mean())
                msg += f' val_acc={acc:.4f}'
            print(msg, flush=True)

    val_out = predict_logits(model, X_val) if (X_val is not None and len(X_val)) else None
    return model, val_out


def predict_logits(model: SymNet, X: np.ndarray, batch_size: int = 512) -> np.ndarray:
    model.eval()
    outs = []
    with torch.no_grad():
        for i in range(0, len(X), batch_size):
            bx = torch.from_numpy(X[i:i + batch_size]).float() / 255.0
            outs.append(model(bx).numpy())
    return np.concatenate(outs, axis=0) if outs else np.zeros((0, len(CLASSES)), np.float32)


def fit_temperature(logits: np.ndarray, labels: np.ndarray) -> float:
    """Fits scalar temperature T minimizing NLL on out-of-fold validation logits."""
    if len(labels) < 50:
        return 1.0
    lt = torch.from_numpy(logits.astype(np.float32))
    yt = torch.from_numpy(labels.astype(np.int64))
    best_t, best_nll = 1.0, float('inf')
    for t in np.linspace(0.45, 2.50, 83):
        nll = float(F.cross_entropy(lt / float(t), yt).item())
        if nll < best_nll:
            best_nll, best_t = nll, float(t)
    return best_t


def main() -> int:
    parser = argparse.ArgumentParser(description='Train local offline SymNet v2 classifier.')
    parser.add_argument('--dev-crops', default=None, help='Clean Dev crops .npz from extract_dev_crops.py')
    parser.add_argument('--out', required=True, help='Output .npz path')
    parser.add_argument('--synth-per-class', type=int, default=1800)
    parser.add_argument('--epochs', type=int, default=18)
    parser.add_argument('--cv-epochs', type=int, default=14)
    parser.add_argument('--batch-size', type=int, default=256)
    parser.add_argument('--cv-folds', type=int, default=5)
    parser.add_argument('--real-upsample-min', type=int, default=500)
    parser.add_argument('--threads', type=int, default=12)
    args = parser.parse_args()

    torch.set_num_threads(args.threads)
    X_syn, Y_syn = generate_synthetic(args.synth_per_class, seed=42)

    X_dev = np.zeros((0, 3, PATCH_SIZE, PATCH_SIZE), np.uint8)
    Y_dev = np.zeros(0, np.int64)
    G_dev = np.array([], dtype=str)
    if args.dev_crops and Path(args.dev_crops).exists():
        d = np.load(args.dev_crops)
        X_dev = d['X'].astype(np.uint8)
        Y_dev = d['Y'].astype(np.int64)
        G_dev = d['G'].astype(str)
        print(f'Loaded {len(Y_dev)} real Clean Dev crops across {len(set(G_dev))} base hymns', flush=True)

    temp = 1.0
    if args.cv_folds >= 2 and len(Y_dev) >= 200:
        uniq = sorted(set(G_dev))
        rng = np.random.default_rng(7)
        rng.shuffle(uniq)
        fold_map = {g: i % args.cv_folds for i, g in enumerate(uniq)}
        folds = np.array([fold_map[g] for g in G_dev])
        oof_logits = np.zeros((len(Y_dev), len(CLASSES)), np.float32)
        for f in range(args.cv_folds):
            tr = np.where(folds != f)[0]
            va = np.where(folds == f)[0]
            X_r_tr, Y_r_tr = upsample_real_train(X_dev[tr], Y_dev[tr], args.real_upsample_min, seed=500 + f)
            print(f'--- SymNet CV Fold {f + 1}/{args.cv_folds}: real_train={len(tr)}(up->{len(Y_r_tr)}) real_val={len(va)} ---', flush=True)
            X_tr = np.concatenate([X_syn, X_r_tr], axis=0)
            Y_tr = np.concatenate([Y_syn, Y_r_tr], axis=0)
            _, val_logits = fit_model(X_tr, Y_tr, args.cv_epochs, args.batch_size, seed=100 + f,
                                      X_val=X_dev[va], Y_val=Y_dev[va])
            oof_logits[va] = val_logits
        preds = oof_logits.argmax(1)
        oof_acc = float((preds == Y_dev).mean())
        temp = fit_temperature(oof_logits, Y_dev)
        print(f'=== SymNet Clean Dev {args.cv_folds}-Fold OOF Accuracy: {oof_acc:.4%} (calibrated T={temp:.3f}) ===', flush=True)
        for cid in sorted(set(Y_dev)):
            m = Y_dev == cid
            p = preds == cid
            tp = int((m & p).sum())
            rec = tp / max(1, int(m.sum()))
            prec = tp / max(1, int(p.sum()))
            f1 = 2 * prec * rec / max(1e-9, prec + rec)
            print(f'  {CLASSES[cid]:14s}: rec={rec:7.2%} prec={prec:7.2%} f1={f1:7.2%} ({int(m.sum()):5d} crops)', flush=True)

    print('--- Training final SymNet v2 on Synthetic + Clean Dev (ZERO holdout crops) ---', flush=True)
    X_r_all, Y_r_all = upsample_real_train(X_dev, Y_dev, args.real_upsample_min, seed=2026)
    X_all = np.concatenate([X_syn, X_r_all], axis=0) if len(Y_dev) else X_syn
    Y_all = np.concatenate([Y_syn, Y_r_all], axis=0) if len(Y_dev) else Y_syn
    final_model, _ = fit_model(X_all, Y_all, args.epochs, args.batch_size, seed=2026)
    out_path = Path(args.out)
    export_npz(final_model, out_path, temperature=temp)
    verify_numpy_parity(final_model, out_path, temp, X_dev if len(X_dev) >= 128 else X_syn)
    return 0


if __name__ == '__main__':
    sys.exit(main())

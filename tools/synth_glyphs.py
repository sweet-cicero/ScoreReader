#!/usr/bin/env python3
"""Synthetic engraved music symbol generator for unit tests and local classifier training.

Renders crisp music symbols from open system fonts (NotoMusic, NotoSerif, LiberationSerif)
plus procedural vector drawing (beams, stems, slurs, ties, tilted ovals, ledger lines),
and applies realistic scan degradations (blur, ink bleed, fading, broken rims, slight tilt,
varying staff-line thickness, and JPEG-like noise).

Outputs 3-channel normalized 32x32 patches covering 3.5 x 3.5 staff spaces:
  ch 0: normalized inverted grayscale ink (0 = white paper, 1 = dark ink)
  ch 1: staff-line-removed ink mask
  ch 2: staff-line geometry mask (1 on staff lines, 0 elsewhere)
"""
from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

PATCH_SIZE = 32
PATCH_SPACES = 3.5

CLASSES = [
    'head_filled',      # 0: quarter / eighth / sixteenth filled notehead
    'head_hollow',      # 1: half notehead (hollow oval)
    'head_whole',       # 2: whole notehead (wide upright-hole oval, no stem)
    'head_breve',       # 3: breve / double-whole reciting note
    'rest_whole',       # 4: whole rest hanging from line 4
    'rest_half',        # 5: half rest sitting on line 3
    'rest_quarter',     # 6: quarter rest
    'rest_eighth',      # 7: eighth rest
    'rest_16th',        # 8: sixteenth rest
    'acc_sharp',        # 9: sharp
    'acc_flat',         # 10: flat
    'acc_natural',      # 11: natural
    'clef_G',           # 12: treble clef
    'clef_F',           # 13: bass clef
    'clef_C',           # 14: alto/tenor C clef
    'dot',              # 15: augmentation dot
    'dynamic',          # 16: dynamic / text mark (p, f, mf, mp, pp, ff)
    'fermata',          # 17: fermata / breath / ornament
    'noise',            # 18: slur, tie, flag loop, beam corner, barline, blank, speck
]
CLASS_TO_ID = {name: idx for idx, name in enumerate(CLASSES)}

TIME_CLASSES = ['2', '3', '4', '6', '8', '9', '12', 'C', 'cut', 'other']
TIME_TO_ID = {name: idx for idx, name in enumerate(TIME_CLASSES)}

NOTO_MUSIC = '/usr/share/fonts/noto/NotoMusic-Regular.ttf'
SERIF_FONTS = [
    '/usr/share/fonts/noto/NotoSerif-Bold.ttf',
    '/usr/share/fonts/noto/NotoSerif-Regular.ttf',
    '/usr/share/fonts/liberation/LiberationSerif-Bold.ttf',
    '/usr/share/fonts/liberation/LiberationSerif-Regular.ttf',
]
ITALIC_FONTS = [
    '/usr/share/fonts/noto/NotoSerif-BoldItalic.ttf',
    '/usr/share/fonts/noto/NotoSerif-Italic.ttf',
    '/usr/share/fonts/liberation/LiberationSerif-BoldItalic.ttf',
    '/usr/share/fonts/liberation/LiberationSerif-Italic.ttf',
]

UNICODE_GLYPHS = {
    'head_filled': '\U0001D158',
    'head_hollow': '\U0001D157',
    'head_whole': '\U0001D15D',
    'head_breve': '\U0001D15C',
    'rest_quarter': '\U0001D13D',
    'rest_eighth': '\U0001D13E',
    'rest_16th': '\U0001D13F',
    'acc_sharp': '\u266F',
    'acc_flat': '\u266D',
    'acc_natural': '\u266E',
    'clef_G': '\U0001D11E',
    'clef_F': '\U0001D122',
    'clef_C': '\U0001D121',
    'fermata': '\U0001D110',
}


def extract_patch(grey: np.ndarray, bare: np.ndarray, staff_rows: list[float], space: float,
                  cx: float, cy: float, size: int = PATCH_SIZE, spaces: float = PATCH_SPACES,
                  levels: tuple[float, float] | None = None) -> np.ndarray:
    """Extracts a normalized 3-channel (3, size, size) float32 patch centered at (cx, cy).

    Channel 0: inverted normalized grayscale ink in [0, 1].
    Channel 1: staff-line-removed bare ink in [0, 1].
    Channel 2: binary staff-line positions in [0, 1].
    """
    half = int(round(0.5 * spaces * space))
    side = 2 * half + 1
    h, w = grey.shape
    x0, y0 = int(round(cx)) - half, int(round(cy)) - half
    x1, y1 = x0 + side, y0 + side

    if levels is None:
        paper = float(np.percentile(grey[::9, ::9], 85)) if grey.size > 100 else 255.0
        dark = float(np.percentile(grey[grey < paper - 20][::7], 20)) if (grey < paper - 20).any() else 20.0
    else:
        dark, paper = levels
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

    # Draw exact staff line positions relative to the crop center
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


def _draw_font_glyph(canvas: np.ndarray, text: str, font_path: str, px_size: int,
                     cx: float, cy: float, angle: float = 0.0) -> None:
    """Draws a centered font glyph onto a uint8 white-background canvas (ink=0)."""
    pad = int(px_size * 2.5)
    img = Image.new('L', (pad, pad), 255)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, px_size)
    draw.text((pad // 2, pad // 2), text, font=font, fill=0, anchor='mm')
    arr = np.array(img)
    ys, xs = np.nonzero(arr < 245)
    if not len(ys):
        return
    crop = arr[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    if abs(angle) > 0.2:
        h, w = crop.shape
        m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
        crop = cv2.warpAffine(crop, m, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=255)
    ch, cw = crop.shape
    y0 = int(round(cy - ch / 2))
    x0 = int(round(cx - cw / 2))
    sy0, sx0 = max(0, -y0), max(0, -x0)
    dy0, dx0 = max(0, y0), max(0, x0)
    h_copy = min(ch - sy0, canvas.shape[0] - dy0)
    w_copy = min(cw - sx0, canvas.shape[1] - dx0)
    if h_copy > 0 and w_copy > 0:
        region = canvas[dy0:dy0 + h_copy, dx0:dx0 + w_copy]
        np.minimum(region, crop[sy0:sy0 + h_copy, sx0:sx0 + w_copy], out=region)


def _degrade_scan(grey: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Applies realistic scanner/print degradations: blur, ink bleed, fading, noise, contrast shift."""
    out = grey.astype(np.float32)
    # Random ink bleed (erosion of white) or thinning (dilation of white)
    mode = rng.choice(['none', 'bleed', 'thin', 'fade'], p=[0.30, 0.28, 0.22, 0.20])
    if mode == 'bleed':
        k = int(rng.choice([2, 3]))
        out = cv2.erode(out, np.ones((k, k), np.uint8))
    elif mode == 'thin':
        k = int(rng.choice([2, 3]))
        out = cv2.dilate(out, np.ones((k, k), np.uint8))
    elif mode == 'fade':
        # Local fading in the center (simulates worn toner on filled heads!)
        h, w = out.shape
        yy, xx = np.mgrid[0:h, 0:w]
        fy = rng.uniform(0.35 * h, 0.65 * h)
        fx = rng.uniform(0.35 * w, 0.65 * w)
        rad = rng.uniform(0.15 * h, 0.4 * h)
        fade = np.exp(-((yy - fy) ** 2 + (xx - fx) ** 2) / (2 * rad * rad))
        out = np.clip(out + rng.uniform(35, 110) * fade, 0, 255)

    # Slight optical blur
    if rng.random() < 0.75:
        sigma = float(rng.uniform(0.35, 1.35))
        out = cv2.GaussianBlur(out, (0, 0), sigma)

    # Contrast / paper tint / dark floor
    dark = float(rng.uniform(0, 65))
    paper = float(rng.uniform(215, 255))
    out = dark + (out / 255.0) * (paper - dark)

    # Additive Gaussian sensor noise + occasional salt-and-pepper specks
    noise = rng.normal(0.0, float(rng.uniform(1.5, 9.0)), out.shape)
    out = np.clip(out + noise, 0, 255)
    return out.astype(np.uint8)


def synthesize_sample(cls_name: str, rng: np.random.Generator) -> np.ndarray:
    """Synthesizes one realistic 3-channel (3, 32, 32) training patch for `cls_name`."""
    space = float(rng.uniform(14.0, 32.0))
    side = int(round(6.5 * space))
    cx, cy = side / 2.0 + rng.uniform(-0.18 * space, 0.18 * space), side / 2.0 + rng.uniform(-0.18 * space, 0.18 * space)
    canvas = np.full((side, side), 255, dtype=np.uint8)
    bare_canvas = np.full((side, side), 255, dtype=np.uint8)

    # Place 5 staff lines relative to symbol's pitch position
    if cls_name == 'rest_whole':
        # Whole rest hangs from line 4 (second line from top -> rows[1])
        line1 = cy - 0.25 * space
        rows = [line1 - space, line1, line1 + space, line1 + 2 * space, line1 + 3 * space]
    elif cls_name == 'rest_half':
        # Half rest sits on line 3 (middle line -> rows[2])
        line2 = cy + 0.25 * space
        rows = [line2 - 2 * space, line2 - space, line2, line2 + space, line2 + 2 * space]
    elif cls_name in ('rest_quarter', 'rest_eighth', 'rest_16th', 'clef_G', 'clef_F', 'clef_C'):
        mid = cy + rng.uniform(-0.4 * space, 0.4 * space)
        rows = [mid + (k - 2) * space for k in range(5)]
    elif cls_name in ('dynamic', 'fermata'):
        above = rng.random() < 0.5
        offset = rng.uniform(1.5, 3.2) * space
        rows = [(cy + offset + k * space) if above else (cy - offset - (4 - k) * space) for k in range(5)]
    else:
        place = int(rng.integers(-6, 7))
        mid = cy + place * 0.5 * space
        rows = [mid + (k - 2) * space for k in range(5)]

    line_thick = max(1, int(round(rng.uniform(0.08, 0.18) * space)))
    stem_thick = max(1, int(round(rng.uniform(0.08, 0.16) * space)))

    def draw_symbol(target: np.ndarray) -> None:
        if cls_name == 'head_filled':
            if rng.random() < 0.45 and Path(NOTO_MUSIC).exists():
                _draw_font_glyph(target, UNICODE_GLYPHS[cls_name], NOTO_MUSIC, int(round(rng.uniform(3.4, 4.4) * space)), cx, cy, rng.uniform(-6, 6))
            else:
                rx = int(round(rng.uniform(0.55, 0.72) * space))
                ry = int(round(rng.uniform(0.38, 0.50) * space))
                ang = float(rng.uniform(-32, -12))
                cv2.ellipse(target, (int(cx), int(cy)), (rx, ry), ang, 0, 360, 0, -1, cv2.LINE_AA)
                if rng.random() < 0.25:
                    # Simulate faded ink core on a filled head (still noticeably grey, NOT crisp white hollow hole)
                    cv2.ellipse(target, (int(cx), int(cy)), (max(1, rx // 2), max(1, ry // 2)), ang, 0, 360, int(rng.uniform(65, 130)), -1, cv2.LINE_AA)
            # Attach stem (up right or down left, sometimes both)
            if rng.random() < 0.92:
                up = rng.random() < 0.5
                sx = int(round(cx + (0.58 if up else -0.58) * space))
                sy_end = int(round(cy + (-3.2 if up else 3.2) * space))
                cv2.line(target, (sx, int(cy)), (sx, sy_end), 0, stem_thick)
            # Occasional neighboring chord head or dot
            if rng.random() < 0.20:
                dy = rng.choice([-1.0, 1.0]) * space
                cv2.ellipse(target, (int(cx), int(cy + dy)), (int(0.6 * space), int(0.42 * space)), -20, 0, 360, 0, -1, cv2.LINE_AA)

        elif cls_name == 'head_hollow':
            if rng.random() < 0.45 and Path(NOTO_MUSIC).exists():
                _draw_font_glyph(target, UNICODE_GLYPHS[cls_name], NOTO_MUSIC, int(round(rng.uniform(3.4, 4.4) * space)), cx, cy, rng.uniform(-6, 6))
            else:
                rx = int(round(rng.uniform(0.58, 0.76) * space))
                ry = int(round(rng.uniform(0.40, 0.52) * space))
                ang = float(rng.uniform(-34, -15))
                cv2.ellipse(target, (int(cx), int(cy)), (rx, ry), ang, 0, 360, 0, -1, cv2.LINE_AA)
                irx = max(2, int(round(rx * rng.uniform(0.55, 0.72))))
                iry = max(1, int(round(ry * rng.uniform(0.32, 0.52))))
                cv2.ellipse(target, (int(cx), int(cy)), (irx, iry), ang, 0, 360, 255, -1, cv2.LINE_AA)
                # Occasional thin/broken rim
                if rng.random() < 0.25:
                    bx = int(round(cx + rng.uniform(-0.4, 0.4) * rx))
                    by = int(round(cy + rng.choice([-1, 1]) * ry))
                    cv2.circle(target, (bx, by), max(1, int(0.12 * space)), 255, -1)
            if rng.random() < 0.95:
                up = rng.random() < 0.5
                sx = int(round(cx + (0.60 if up else -0.60) * space))
                sy_end = int(round(cy + (-3.2 if up else 3.2) * space))
                cv2.line(target, (sx, int(cy)), (sx, sy_end), 0, stem_thick)

        elif cls_name == 'head_whole':
            if rng.random() < 0.55 and Path(NOTO_MUSIC).exists():
                _draw_font_glyph(target, UNICODE_GLYPHS[cls_name], NOTO_MUSIC, int(round(rng.uniform(3.4, 4.4) * space)), cx, cy, rng.uniform(-4, 4))
            else:
                rx = int(round(rng.uniform(0.72, 0.95) * space))
                ry = int(round(rng.uniform(0.44, 0.55) * space))
                cv2.ellipse(target, (int(cx), int(cy)), (rx, ry), 0, 0, 360, 0, -1, cv2.LINE_AA)
                cv2.ellipse(target, (int(cx), int(cy)), (max(2, int(0.42 * rx)), max(2, int(0.68 * ry))), float(rng.uniform(15, 35)), 0, 360, 255, -1, cv2.LINE_AA)

        elif cls_name == 'head_breve':
            if rng.random() < 0.5 and Path(NOTO_MUSIC).exists():
                _draw_font_glyph(target, UNICODE_GLYPHS[cls_name], NOTO_MUSIC, int(round(rng.uniform(3.4, 4.4) * space)), cx, cy)
            else:
                rx = int(round(rng.uniform(0.75, 0.95) * space))
                ry = int(round(rng.uniform(0.44, 0.54) * space))
                cv2.ellipse(target, (int(cx), int(cy)), (rx, ry), 0, 0, 360, 0, -1, cv2.LINE_AA)
                cv2.ellipse(target, (int(cx), int(cy)), (max(2, int(0.45 * rx)), max(2, int(0.65 * ry))), 20, 0, 360, 255, -1, cv2.LINE_AA)
                bar_h = int(round(rng.uniform(0.65, 0.95) * space))
                for side_x in (int(cx - rx - 0.15 * space), int(cx + rx + 0.15 * space)):
                    cv2.line(target, (side_x, int(cy - bar_h)), (side_x, int(cy + bar_h)), 0, stem_thick)

        elif cls_name in ('rest_whole', 'rest_half'):
            rw = int(round(rng.uniform(0.95, 1.35) * space))
            rh = int(round(rng.uniform(0.40, 0.56) * space))
            x0, x1 = int(round(cx - rw / 2)), int(round(cx + rw / 2))
            if cls_name == 'rest_whole':
                y0 = int(round(rows[1]))
                cv2.rectangle(target, (x0, y0), (x1, y0 + rh), 0, -1)
            else:
                y1 = int(round(rows[2]))
                cv2.rectangle(target, (x0, y1 - rh), (x1, y1), 0, -1)

        elif cls_name in ('rest_quarter', 'rest_eighth', 'rest_16th', 'acc_sharp', 'acc_flat', 'acc_natural', 'clef_G', 'clef_F', 'clef_C', 'fermata'):
            scale_map = {
                'rest_quarter': (3.5, 4.8), 'rest_eighth': (3.2, 4.5), 'rest_16th': (3.5, 4.8),
                'acc_sharp': (3.0, 4.4), 'acc_flat': (3.2, 4.5), 'acc_natural': (3.0, 4.4),
                'clef_G': (3.6, 4.6), 'clef_F': (3.4, 4.4), 'clef_C': (3.6, 4.5), 'fermata': (3.2, 4.4),
            }
            lo, hi = scale_map[cls_name]
            px = int(round(rng.uniform(lo, hi) * space))
            _draw_font_glyph(target, UNICODE_GLYPHS[cls_name], NOTO_MUSIC, px, cx, cy, rng.uniform(-5, 5))
            # Sometimes place a notehead to the right of an accidental
            if cls_name.startswith('acc_') and rng.random() < 0.55:
                nx = int(round(cx + rng.uniform(1.15, 1.65) * space))
                cv2.ellipse(target, (nx, int(cy)), (int(0.6 * space), int(0.42 * space)), -20, 0, 360, 0, -1, cv2.LINE_AA)

        elif cls_name == 'dot':
            r = max(2, int(round(rng.uniform(0.14, 0.24) * space)))
            cv2.circle(target, (int(cx), int(cy)), r, 0, -1, cv2.LINE_AA)
            if rng.random() < 0.7:
                nx = int(round(cx - rng.uniform(0.9, 1.35) * space))
                cv2.ellipse(target, (nx, int(cy)), (int(0.6 * space), int(0.42 * space)), -20, 0, 360, 0, -1, cv2.LINE_AA)

        elif cls_name == 'dynamic':
            text = str(rng.choice(['p', 'f', 'mf', 'mp', 'pp', 'ff', 'sfz', 'cresc.']))
            font = str(rng.choice(ITALIC_FONTS))
            px = int(round(rng.uniform(1.1, 2.0) * space))
            _draw_font_glyph(target, text, font, px, cx, cy, rng.uniform(-4, 4))

        elif cls_name == 'noise':
            kind = rng.choice(['blank', 'barline', 'slur', 'beam', 'flag_loop', 'speck', 'letter'])
            if kind == 'barline':
                cv2.line(target, (int(cx), int(rows[0])), (int(cx), int(rows[4])), 0, max(1, int(0.12 * space)))
            elif kind == 'slur':
                cv2.ellipse(target, (int(cx), int(cy + 0.8 * space)), (int(1.6 * space), int(0.7 * space)), 0, 190, 350, 0, max(1, int(0.15 * space)), cv2.LINE_AA)
            elif kind == 'beam':
                pts = np.array([
                    [int(cx - 1.5 * space), int(cy - 0.3 * space)],
                    [int(cx + 1.5 * space), int(cy + 0.1 * space)],
                    [int(cx + 1.5 * space), int(cy + 0.6 * space)],
                    [int(cx - 1.5 * space), int(cy + 0.2 * space)],
                ], np.int32)
                cv2.fillPoly(target, [pts], 0)
            elif kind == 'flag_loop':
                cv2.line(target, (int(cx - 0.3 * space), int(cy - 1.5 * space)), (int(cx - 0.3 * space), int(cy + 1.5 * space)), 0, stem_thick)
                cv2.ellipse(target, (int(cx + 0.15 * space), int(cy)), (int(0.45 * space), int(0.75 * space)), 10, -90, 90, 0, max(2, int(0.22 * space)), cv2.LINE_AA)
            elif kind == 'speck':
                for _ in range(int(rng.integers(1, 5))):
                    sx = int(cx + rng.uniform(-0.8, 0.8) * space)
                    sy = int(cy + rng.uniform(-0.8, 0.8) * space)
                    cv2.circle(target, (sx, sy), max(1, int(rng.uniform(0.06, 0.14) * space)), 0, -1)
            elif kind == 'letter':
                ch = str(rng.choice(list('aeonrstbdhpgyAEGHMNRST')))
                font = str(rng.choice(SERIF_FONTS))
                _draw_font_glyph(target, ch, font, int(round(rng.uniform(1.0, 1.8) * space)), cx, cy)

    draw_symbol(bare_canvas)
    draw_symbol(canvas)
    # Draw staff lines on full canvas (not on bare_canvas)
    for row in rows:
        ry = int(round(row))
        if 0 <= ry < side:
            cv2.line(canvas, (0, ry), (side - 1, ry), int(rng.uniform(0, 75)), line_thick)

    degraded = _degrade_scan(canvas, rng)
    bare_mask = (bare_canvas < 200).astype(np.uint8)
    return extract_patch(degraded, bare_mask, rows, space, cx, cy, levels=(20.0, 245.0))


if __name__ == '__main__':
    rng = np.random.default_rng(42)
    for name in CLASSES:
        p = synthesize_sample(name, rng)
        assert p.shape == (3, PATCH_SIZE, PATCH_SIZE) and p.dtype == np.float32
    print(f'ok: synthesized all {len(CLASSES)} classes with shape (3, {PATCH_SIZE}, {PATCH_SIZE})')

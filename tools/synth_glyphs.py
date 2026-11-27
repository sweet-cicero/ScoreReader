#!/usr/bin/env python3
"""Synthetic engraved music symbol generator for unit tests and local classifier training.

Renders crisp music symbols from open system fonts (NotoMusic, NotoSerif, LiberationSerif)
and procedural vector drawing (beams, stems, slurs, ties, tilted ovals, ledger lines,
slim engraved quarter rests, ledger-line half/whole rests, compact eighth rests,
fermatas, dynamics, touching chords, and down-stemmed notes).

Outputs 3-channel normalized 32x32 patches covering 3.5 x 3.5 staff spaces via the exact
scorereader.classify.extract_patch function:
  ch 0: normalized inverted grayscale ink (0 = white paper, 1 = dark ink)
  ch 1: staff-line-removed bare ink mask
  ch 2: staff-line geometry mask (1 on staff lines, 0 elsewhere)
"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scorereader.classify import (
    CLASSES as _CLASS_TUPLE,
    CLASS_TO_ID,
    PATCH_SIZE,
    PATCH_SPACES,
    extract_patch,
)

CLASSES = list(_CLASS_TUPLE)

TIME_CLASSES = ['2', '3', '4', '6', '8', '9', '12', 'C', 'cut', 'other']
TIME_TO_ID = {name: idx for idx, name in enumerate(TIME_CLASSES)}

NOTO_MUSIC = '/usr/share/fonts/noto/NotoMusic-Regular.ttf'
SERIF_FONTS = [
    p for p in (
        '/usr/share/fonts/noto/NotoSerif-Bold.ttf',
        '/usr/share/fonts/noto/NotoSerif-Regular.ttf',
        '/usr/share/fonts/liberation/LiberationSerif-Bold.ttf',
        '/usr/share/fonts/liberation/LiberationSerif-Regular.ttf',
        '/usr/share/fonts/noto/NotoSans-Bold.ttf',
    ) if Path(p).exists()
]
ITALIC_FONTS = [
    p for p in (
        '/usr/share/fonts/noto/NotoSerif-BoldItalic.ttf',
        '/usr/share/fonts/noto/NotoSerif-Italic.ttf',
        '/usr/share/fonts/liberation/LiberationSerif-BoldItalic.ttf',
        '/usr/share/fonts/liberation/LiberationSerif-Italic.ttf',
        '/usr/share/fonts/noto/NotoSans-BoldItalic.ttf',
    ) if Path(p).exists()
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

_FONT_CACHE: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def _get_font(font_path: str, px_size: int) -> ImageFont.FreeTypeFont:
    key = (font_path, max(8, int(px_size)))
    font = _FONT_CACHE.get(key)
    if font is None:
        font = ImageFont.truetype(font_path, key[1])
        _FONT_CACHE[key] = font
    return font


def _draw_font_glyph(canvas: np.ndarray, text: str, font_path: str, px_size: int,
                     cx: float, cy: float, angle: float = 0.0,
                     scale_x: float = 1.0, scale_y: float = 1.0) -> None:
    """Draws a centered font glyph onto a uint8 white-background canvas (ink=0)."""
    pad = max(32, int(px_size * 2.5))
    img = Image.new('L', (pad, pad), 255)
    draw = ImageDraw.Draw(img)
    font = _get_font(font_path, px_size)
    draw.text((pad // 2, pad // 2), text, font=font, fill=0, anchor='mm')
    arr = np.array(img)
    ys, xs = np.nonzero(arr < 245)
    if not len(ys):
        return
    crop = arr[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    if abs(scale_x - 1.0) > 0.02 or abs(scale_y - 1.0) > 0.02:
        ch, cw = crop.shape
        nw = max(2, int(round(cw * scale_x)))
        nh = max(2, int(round(ch * scale_y)))
        crop = cv2.resize(crop, (nw, nh), interpolation=cv2.INTER_AREA if (nw < cw or nh < ch) else cv2.INTER_LINEAR)
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


def _degrade_scan_levels(grey: np.ndarray, rng: np.random.Generator,
                         bare: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray | None, tuple[float, float]]:
    """Applies matched scanner and print degradations to grey and optional bare canvases."""
    out = grey.astype(np.float32)
    bout = bare.astype(np.float32) if bare is not None else None
    mode = str(rng.choice(['none', 'bleed', 'thin', 'fade'], p=[0.28, 0.28, 0.22, 0.22]))
    if mode == 'bleed':
        k = int(rng.choice([2, 3]))
        kern = np.ones((k, k), np.uint8)
        out = cv2.erode(out, kern)
        if bout is not None:
            bout = cv2.erode(bout, kern)
    elif mode == 'thin':
        k = int(rng.choice([2, 3]))
        kern = np.ones((k, k), np.uint8)
        out = cv2.dilate(out, kern)
        if bout is not None:
            bout = cv2.dilate(bout, kern)
    elif mode == 'fade':
        h, w = out.shape
        yy, xx = np.mgrid[0:h, 0:w]
        fy = float(rng.uniform(0.32 * h, 0.68 * h))
        fx = float(rng.uniform(0.32 * w, 0.68 * w))
        rad = float(rng.uniform(0.14 * h, 0.38 * h))
        fade = np.exp(-((yy - fy) ** 2 + (xx - fx) ** 2) / (2 * rad * rad))
        amp = float(rng.uniform(30, 105))
        out = np.clip(out + amp * fade, 0, 255)
        if bout is not None:
            bout = np.clip(bout + 0.7 * amp * fade, 0, 255)

    if rng.random() < 0.75:
        sigma = float(rng.uniform(0.35, 1.30))
        out = cv2.GaussianBlur(out, (0, 0), sigma)
        if bout is not None:
            bout = cv2.GaussianBlur(bout, (0, 0), min(0.9, sigma))

    dark = float(rng.uniform(0, 62))
    paper = float(rng.uniform(218, 255))
    out = dark + (out / 255.0) * (paper - dark)
    noise = rng.normal(0.0, float(rng.uniform(1.5, 8.5)), out.shape)
    out = np.clip(out + noise, 0, 255).astype(np.uint8)

    # Slight level jitter matches real page-level percentile estimation.
    lv_dark = float(np.clip(dark + rng.uniform(-6.0, 6.0), 0.0, 100.0))
    lv_paper = float(np.clip(paper + rng.uniform(-5.0, 5.0), lv_dark + 40.0, 255.0))
    if bout is not None:
        thresh = float(rng.uniform(175.0, 215.0))
        bmask = (bout < thresh).astype(np.uint8)
        return out, bmask, (lv_dark, lv_paper)
    return out, None, (lv_dark, lv_paper)


def _degrade_scan(grey: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Applies realistic scanner and print degradations to one grayscale canvas."""
    out, _, _ = _degrade_scan_levels(grey, rng, bare=None)
    return out


def _draw_ledgers(target: np.ndarray, rows: list[float], space: float, cx: float, cy: float,
                  half_w: float, line_thick: int) -> None:
    """Draws horizontal ledger lines for notes or rests placed outside the five staff lines."""
    x0 = int(round(cx - half_w))
    x1 = int(round(cx + half_w))
    top_line, bot_line = rows[0], rows[4]
    if cy <= top_line - 0.8 * space:
        step = 1
        while top_line - step * space >= cy - 0.35 * space and step <= 4:
            ly = int(round(top_line - step * space))
            if 0 <= ly < target.shape[0]:
                cv2.line(target, (x0, ly), (x1, ly), 0, line_thick)
            step += 1
    elif cy >= bot_line + 0.8 * space:
        step = 1
        while bot_line + step * space <= cy + 0.35 * space and step <= 4:
            ly = int(round(bot_line + step * space))
            if 0 <= ly < target.shape[0]:
                cv2.line(target, (x0, ly), (x1, ly), 0, line_thick)
            step += 1


def _draw_filled_head(target: np.ndarray, cx: float, cy: float, space: float, rng: np.random.Generator) -> tuple[int, int]:
    """Draws a realistic filled notehead with optional worn center or notched edge."""
    rx = int(round(rng.uniform(0.53, 0.72) * space))
    ry = int(round(rng.uniform(0.37, 0.50) * space))
    ang = float(rng.uniform(-34, -10))
    if rng.random() < 0.38 and Path(NOTO_MUSIC).exists():
        _draw_font_glyph(target, UNICODE_GLYPHS['head_filled'], NOTO_MUSIC,
                         int(round(rng.uniform(3.3, 4.4) * space)), cx, cy,
                         rng.uniform(-6, 6), scale_x=float(rng.uniform(0.9, 1.1)))
    else:
        cv2.ellipse(target, (int(round(cx)), int(round(cy))), (rx, ry), ang, 0, 360, 0, -1, cv2.LINE_AA)
    if rng.random() < 0.28:
        # Faded toner core remains dark grey so filled heads stay distinct from hollow heads.
        irx = max(1, int(round(rx * rng.uniform(0.35, 0.55))))
        iry = max(1, int(round(ry * rng.uniform(0.30, 0.50))))
        cv2.ellipse(target, (int(round(cx)), int(round(cy))), (irx, iry), ang, 0, 360,
                    int(rng.uniform(55, 135)), -1, cv2.LINE_AA)
    if rng.random() < 0.14:
        # Tiny pinpoint speck from worn scan on filled head.
        sx = int(round(cx + rng.uniform(-0.25, 0.25) * rx))
        sy = int(round(cy + rng.uniform(-0.25, 0.25) * ry))
        cv2.circle(target, (sx, sy), max(1, int(round(0.08 * space))), int(rng.uniform(160, 230)), -1)
    if rng.random() < 0.14:
        # Small edge notch from worn engraving.
        nx = int(round(cx + rng.choice([-1, 1]) * rx * 0.85))
        ny = int(round(cy + rng.uniform(-0.4, 0.4) * ry))
        cv2.circle(target, (nx, ny), max(1, int(round(0.11 * space))), 255, -1)
    return rx, ry


def _draw_hollow_head(target: np.ndarray, cx: float, cy: float, space: float, rng: np.random.Generator) -> tuple[int, int]:
    """Draws a realistic hollow half notehead with optional narrow slit or broken rim."""
    rx = int(round(rng.uniform(0.56, 0.77) * space))
    ry = int(round(rng.uniform(0.38, 0.52) * space))
    ang = float(rng.uniform(-35, -14))
    if rng.random() < 0.38 and Path(NOTO_MUSIC).exists():
        _draw_font_glyph(target, UNICODE_GLYPHS['head_hollow'], NOTO_MUSIC,
                         int(round(rng.uniform(3.3, 4.4) * space)), cx, cy,
                         rng.uniform(-6, 6), scale_x=float(rng.uniform(0.9, 1.12)))
    else:
        cv2.ellipse(target, (int(round(cx)), int(round(cy))), (rx, ry), ang, 0, 360, 0, -1, cv2.LINE_AA)
        slit = rng.random() < 0.22
        irx = max(2, int(round(rx * rng.uniform(0.52, 0.72))))
        iry = max(1, int(round(ry * (rng.uniform(0.20, 0.34) if slit else rng.uniform(0.35, 0.54)))))
        cv2.ellipse(target, (int(round(cx)), int(round(cy))), (irx, iry), ang, 0, 360, 255, -1, cv2.LINE_AA)
    if rng.random() < 0.26:
        # Simulate broken rim on a light copy.
        side = str(rng.choice(['top', 'bot', 'left', 'right']))
        if side in ('top', 'bot'):
            bx = int(round(cx + rng.uniform(-0.35, 0.35) * rx))
            by = int(round(cy + (-1 if side == 'top' else 1) * ry * 0.92))
        else:
            bx = int(round(cx + (-1 if side == 'left' else 1) * rx * 0.92))
            by = int(round(cy + rng.uniform(-0.35, 0.35) * ry))
        cv2.circle(target, (bx, by), max(1, int(round(rng.uniform(0.10, 0.18) * space))), 255, -1)
    return rx, ry


def _draw_slim_quarter_rest(target: np.ndarray, cx: float, cy: float, space: float,
                            rng: np.random.Generator, style: str) -> None:
    """Draws slim engraved or autographed zigzag quarter rests."""
    h = float(rng.uniform(2.25, 3.25) * space)
    if style == 'slim':
        w = float(rng.uniform(0.40, 0.65) * space)
        thin_t = max(1, int(round(rng.uniform(0.08, 0.16) * space)))
        mid_t = max(2, int(round(rng.uniform(0.18, 0.32) * space)))
    else:
        w = float(rng.uniform(0.48, 0.88) * space)
        thin_t = max(1, int(round(rng.uniform(0.09, 0.18) * space)))
        mid_t = max(2, int(round(rng.uniform(0.14, 0.28) * space)))
    y0 = cy - 0.5 * h
    pts = [
        (cx - 0.18 * w, y0 + 0.02 * h),
        (cx + 0.42 * w, y0 + 0.26 * h),
        (cx - 0.32 * w, y0 + 0.52 * h),
        (cx + 0.38 * w, y0 + 0.74 * h),
        (cx - 0.34 * w, y0 + 0.82 * h),
        (cx - 0.44 * w, y0 + 0.92 * h),
        (cx + 0.14 * w, y0 + 0.99 * h),
    ]
    ip = [(int(round(px)), int(round(py))) for px, py in pts]
    cv2.line(target, ip[0], ip[1], 0, thin_t, cv2.LINE_AA)
    cv2.line(target, ip[1], ip[2], 0, mid_t, cv2.LINE_AA)
    cv2.line(target, ip[2], ip[3], 0, thin_t, cv2.LINE_AA)
    # Curved bottom C-hook sweeping left and down.
    hook = np.array([ip[3], ip[4], ip[5], ip[6]], np.int32)
    cv2.polylines(target, [hook], False, 0, max(1, int(round(0.75 * mid_t))), cv2.LINE_AA)


def _draw_cross_quarter_rest(target: np.ndarray, cx: float, cy: float, space: float,
                             rng: np.random.Generator) -> None:
    """Draws an older X-shaped printed quarter rest with a short central upright."""
    h = float(rng.uniform(1.95, 2.45) * space)
    w = float(rng.uniform(1.25, 1.75) * space)
    t = max(2, int(round(rng.uniform(0.14, 0.24) * space)))
    cv2.line(target, (int(round(cx - 0.48 * w)), int(round(cy - 0.48 * h))),
             (int(round(cx + 0.48 * w)), int(round(cy + 0.48 * h))), 0, t, cv2.LINE_AA)
    cv2.line(target, (int(round(cx + 0.48 * w)), int(round(cy - 0.48 * h))),
             (int(round(cx - 0.48 * w)), int(round(cy + 0.48 * h))), 0, t, cv2.LINE_AA)
    cv2.line(target, (int(round(cx)), int(round(cy - 0.38 * h))),
             (int(round(cx)), int(round(cy + 0.38 * h))), 0, max(1, t - 1), cv2.LINE_AA)


def _draw_procedural_eighth_rest(target: np.ndarray, cx: float, cy: float, space: float,
                                 rng: np.random.Generator, compact: bool, double: bool = False) -> None:
    """Draws compact or standard engraved eighth and sixteenth rests."""
    if double:
        h = float(rng.uniform(1.9, 3.0) * space)
        w = float(rng.uniform(0.68, 1.20) * space)
    elif compact:
        h = float(rng.uniform(1.10, 1.50) * space)
        w = float(rng.uniform(0.52, 0.95) * space)
    else:
        h = float(rng.uniform(1.50, 2.35) * space)
        w = float(rng.uniform(0.60, 1.15) * space)
    y0 = cy - 0.5 * h
    x_tr = cx + 0.42 * w
    x_bl = cx - 0.30 * w
    stem_t = max(1, int(round(rng.uniform(0.10, 0.19) * space)))
    cv2.line(target, (int(round(x_tr)), int(round(y0 + 0.08 * h))),
             (int(round(x_bl)), int(round(y0 + 0.96 * h))), 0, stem_t, cv2.LINE_AA)
    bulbs = [0.18, 0.52] if double else [0.22]
    for frac in bulbs:
        by = y0 + frac * h
        bx = cx - 0.24 * w + (0.06 * w if frac > 0.3 else 0.0)
        br = max(2, int(round(rng.uniform(0.16, 0.26) * space)))
        cv2.circle(target, (int(round(bx)), int(round(by))), br, 0, -1, cv2.LINE_AA)
        hx = x_tr - (0.14 * w if frac > 0.3 else 0.0)
        pts = np.array([
            [int(round(bx)), int(round(by + 0.3 * br))],
            [int(round(0.5 * (bx + hx))), int(round(by + 0.22 * space))],
            [int(round(hx)), int(round(by - 0.05 * space))],
        ], np.int32)
        cv2.polylines(target, [pts], False, 0, stem_t, cv2.LINE_AA)


def _draw_procedural_fermata(target: np.ndarray, cx: float, cy: float, space: float,
                             rng: np.random.Generator, dome: bool) -> None:
    """Draws a realistic engraved fermata arc and centered dot."""
    w = float(rng.uniform(1.65, 3.20) * space)
    h = float(rng.uniform(0.85, 1.75) * space)
    rx, ry = int(round(0.5 * w)), int(round(0.82 * h))
    # Build tapered crescent by filling outer ellipse and subtracting shifted inner ellipse.
    sign = 1 if dome else -1
    base_y = int(round(cy + sign * 0.35 * h))
    mask = np.zeros(target.shape, dtype=np.uint8)
    start_a, end_a = (180, 360) if dome else (0, 180)
    cv2.ellipse(mask, (int(round(cx)), base_y), (rx, ry), 0, start_a, end_a, 255, -1, cv2.LINE_AA)
    inner_shift = max(2, int(round(rng.uniform(0.18, 0.30) * space)))
    cv2.ellipse(mask, (int(round(cx)), base_y + sign * inner_shift),
                (max(2, int(round(rx * 0.88))), max(2, int(round(ry * 0.86)))),
                0, start_a, end_a, 0, -1, cv2.LINE_AA)
    target[mask > 127] = 0
    dot_r = max(2, int(round(rng.uniform(0.14, 0.24) * space)))
    dot_y = int(round(base_y - sign * rng.uniform(0.10, 0.30) * h))
    cv2.circle(target, (int(round(cx)), dot_y), dot_r, 0, -1, cv2.LINE_AA)


def _draw_procedural_accidental(target: np.ndarray, cls_name: str, cx: float, cy: float,
                                space: float, rng: np.random.Generator) -> None:
    """Draws engraved sharp, flat, or natural accidentals procedurally."""
    thin = max(1, int(round(rng.uniform(0.09, 0.16) * space)))
    bar = max(2, int(round(rng.uniform(0.18, 0.30) * space)))
    if cls_name == 'acc_sharp':
        dx = float(rng.uniform(0.22, 0.34) * space)
        hh = float(rng.uniform(0.95, 1.35) * space)
        cv2.line(target, (int(cx - dx), int(cy - hh)), (int(cx - dx), int(cy + hh)), 0, thin, cv2.LINE_AA)
        cv2.line(target, (int(cx + dx), int(cy - hh)), (int(cx + dx), int(cy + hh)), 0, thin, cv2.LINE_AA)
        for dy in (-0.36 * space, 0.36 * space):
            cv2.line(target, (int(cx - 0.55 * space), int(cy + dy + 0.12 * space)),
                     (int(cx + 0.55 * space), int(cy + dy - 0.12 * space)), 0, bar, cv2.LINE_AA)
    elif cls_name == 'acc_flat':
        sx = int(round(cx - 0.22 * space))
        cv2.line(target, (sx, int(cy - 1.55 * space)), (sx, int(cy + 0.65 * space)), 0, thin, cv2.LINE_AA)
        pts = np.array([
            [sx, int(cy - 0.18 * space)],
            [int(cx + 0.34 * space), int(cy - 0.32 * space)],
            [int(cx + 0.42 * space), int(cy + 0.10 * space)],
            [sx, int(cy + 0.62 * space)],
        ], np.int32)
        cv2.polylines(target, [pts], False, 0, bar, cv2.LINE_AA)
    else:
        dx = float(rng.uniform(0.20, 0.32) * space)
        cv2.line(target, (int(cx - dx), int(cy - 1.25 * space)), (int(cx - dx), int(cy + 0.55 * space)), 0, thin, cv2.LINE_AA)
        cv2.line(target, (int(cx + dx), int(cy - 0.55 * space)), (int(cx + dx), int(cy + 1.25 * space)), 0, thin, cv2.LINE_AA)
        cv2.line(target, (int(cx - dx), int(cy - 0.34 * space)), (int(cx + dx), int(cy - 0.48 * space)), 0, bar, cv2.LINE_AA)
        cv2.line(target, (int(cx - dx), int(cy + 0.48 * space)), (int(cx + dx), int(cy + 0.34 * space)), 0, bar, cv2.LINE_AA)


def synthesize_sample(cls_name: str, rng: np.random.Generator) -> np.ndarray:
    """Synthesizes one realistic 3-channel (3, 32, 32) training patch for cls_name."""
    space = float(rng.uniform(14.0, 32.0))
    side = int(round(7.0 * space))
    cx = side / 2.0 + float(rng.uniform(-0.18 * space, 0.18 * space))
    cy = side / 2.0 + float(rng.uniform(-0.18 * space, 0.18 * space))
    canvas = np.full((side, side), 255, dtype=np.uint8)
    bare_canvas = np.full((side, side), 255, dtype=np.uint8)

    ledger_rest = False
    ledger_line_y = 0.0
    place = 0

    # Place five staff lines relative to the target symbol position.
    if cls_name == 'rest_whole':
        if rng.random() < 0.35:
            ledger_rest = True
            above = rng.random() < 0.5
            mid_shift = float(rng.uniform(2.5, 3.4) * (-1 if above else 1))
            # Whole rest hangs below its ledger bar at cy - 0.24*space.
            ledger_line_y = cy - 0.24 * space
            staff_mid = cy - mid_shift * space
            rows = [staff_mid + (k - 2) * space for k in range(5)]
        else:
            line1 = cy - 0.24 * space
            rows = [line1 - space, line1, line1 + space, line1 + 2 * space, line1 + 3 * space]
    elif cls_name == 'rest_half':
        if rng.random() < 0.35:
            ledger_rest = True
            above = rng.random() < 0.5
            mid_shift = float(rng.uniform(2.5, 3.4) * (-1 if above else 1))
            # Half rest sits on top of its ledger bar at cy + 0.24*space.
            ledger_line_y = cy + 0.24 * space
            staff_mid = cy - mid_shift * space
            rows = [staff_mid + (k - 2) * space for k in range(5)]
        else:
            line2 = cy + 0.24 * space
            rows = [line2 - 2 * space, line2 - space, line2, line2 + space, line2 + 2 * space]
    elif cls_name in ('rest_quarter', 'rest_eighth', 'rest_16th'):
        if rng.random() < 0.40:
            # Shifted single-voice rest up to +-3.1 spaces from staff middle.
            shift = float(rng.uniform(0.85, 3.10) * rng.choice([-1, 1]))
            mid = cy - shift * space
        else:
            mid = cy + float(rng.uniform(-0.45 * space, 0.45 * space))
        rows = [mid + (k - 2) * space for k in range(5)]
    elif cls_name in ('clef_G', 'clef_F', 'clef_C'):
        mid = cy + float(rng.uniform(-0.35 * space, 0.35 * space))
        rows = [mid + (k - 2) * space for k in range(5)]
    elif cls_name in ('dynamic', 'fermata'):
        above = rng.random() < 0.5
        offset = float(rng.uniform(1.1, 3.2) * space)
        rows = [(cy + offset + k * space) if above else (cy - offset - (4 - k) * space) for k in range(5)]
    else:
        place = int(rng.integers(-8, 9))
        mid = cy + place * 0.5 * space
        rows = [mid + (k - 2) * space for k in range(5)]

    line_thick = max(1, int(round(rng.uniform(0.08, 0.18) * space)))
    stem_thick = max(1, int(round(rng.uniform(0.08, 0.16) * space)))
    beam_thick = max(2, int(round(rng.uniform(0.34, 0.54) * space)))

    # Draw deterministic symbol instructions onto both bare_canvas and canvas.
    # Use a fixed local seed so both layers receive identical symbol geometry.
    sym_seed = int(rng.integers(0, 2**31 - 1))

    def draw_symbol(target: np.ndarray) -> None:
        lr = np.random.default_rng(sym_seed)

        if cls_name == 'head_filled':
            rx, ry = _draw_filled_head(target, cx, cy, space, lr)
            if abs(place) >= 6:
                _draw_ledgers(target, rows, space, cx, cy, 0.95 * space, line_thick)
            # Attach stem up, stem down, or both (unison).
            stem_roll = lr.random()
            if stem_roll < 0.93:
                up = stem_roll < 0.46
                both = stem_roll > 0.84
                dirs = ['up', 'down'] if both else (['up'] if up else ['down'])
                for d in dirs:
                    sx = int(round(cx + (0.58 if d == 'up' else -0.58) * space))
                    sy_end = int(round(cy + (-3.2 if d == 'up' else 3.2) * space))
                    cv2.line(target, (sx, int(round(cy))), (sx, sy_end), 0, stem_thick)
                    # Optional beam or flag on stem tip (including down-stemmed flags near head).
                    if lr.random() < 0.25:
                        slope = float(lr.uniform(-0.2, 0.2))
                        bx1 = int(round(sx + lr.choice([-1, 1]) * 1.8 * space))
                        by1 = int(round(sy_end + slope * (bx1 - sx)))
                        pts = np.array([[sx, sy_end], [bx1, by1], [bx1, by1 + beam_thick], [sx, sy_end + beam_thick]], np.int32)
                        cv2.fillPoly(target, [pts], 0)
            # Touching chords: 3rd apart, 2nd apart, or neighbor filled/hollow head.
            chord_roll = lr.random()
            if chord_roll < 0.32:
                if chord_roll < 0.14:
                    # 2nd apart touching head (shifted sideways by 1.05..1.20*space).
                    dy = float(lr.choice([-0.5, 0.5]) * space)
                    dx = float(lr.choice([-1.12, 1.12]) * space)
                else:
                    # 3rd or 4th apart stacked chord head.
                    dy = float(lr.choice([-1.0, 1.0, -1.5, 1.5]) * space)
                    dx = 0.0
                if lr.random() < 0.25:
                    _draw_hollow_head(target, cx + dx, cy + dy, space, lr)
                else:
                    cv2.ellipse(target, (int(round(cx + dx)), int(round(cy + dy))), (rx, ry), -20, 0, 360, 0, -1, cv2.LINE_AA)
            if lr.random() < 0.14:
                cv2.circle(target, (int(round(cx + 1.05 * space)), int(round(cy - 0.1 * space))),
                           max(2, int(round(0.18 * space))), 0, -1, cv2.LINE_AA)

        elif cls_name == 'head_hollow':
            rx, ry = _draw_hollow_head(target, cx, cy, space, lr)
            if abs(place) >= 6:
                _draw_ledgers(target, rows, space, cx, cy, 0.98 * space, line_thick)
            if lr.random() < 0.95:
                up = lr.random() < 0.5
                sx = int(round(cx + (0.60 if up else -0.60) * space))
                sy_end = int(round(cy + (-3.2 if up else 3.2) * space))
                cv2.line(target, (sx, int(round(cy))), (sx, sy_end), 0, stem_thick)
            # Optional touching chord head (2nd or 3rd apart).
            if lr.random() < 0.26:
                if lr.random() < 0.45:
                    dy = float(lr.choice([-0.5, 0.5]) * space)
                    dx = float(lr.choice([-1.15, 1.15]) * space)
                else:
                    dy = float(lr.choice([-1.0, 1.0]) * space)
                    dx = 0.0
                if lr.random() < 0.35:
                    _draw_filled_head(target, cx + dx, cy + dy, space, lr)
                else:
                    _draw_hollow_head(target, cx + dx, cy + dy, space, lr)
            if lr.random() < 0.16:
                cv2.circle(target, (int(round(cx + 1.08 * space)), int(round(cy - 0.1 * space))),
                           max(2, int(round(0.18 * space))), 0, -1, cv2.LINE_AA)

        elif cls_name == 'head_whole':
            if lr.random() < 0.50 and Path(NOTO_MUSIC).exists():
                _draw_font_glyph(target, UNICODE_GLYPHS['head_whole'], NOTO_MUSIC,
                                 int(round(lr.uniform(3.4, 4.4) * space)), cx, cy, lr.uniform(-4, 4))
            else:
                rx = int(round(lr.uniform(0.72, 0.96) * space))
                ry = int(round(lr.uniform(0.43, 0.56) * space))
                cv2.ellipse(target, (int(round(cx)), int(round(cy))), (rx, ry), 0, 0, 360, 0, -1, cv2.LINE_AA)
                cv2.ellipse(target, (int(round(cx)), int(round(cy))),
                            (max(2, int(0.42 * rx)), max(2, int(0.68 * ry))),
                            float(lr.uniform(12, 36)), 0, 360, 255, -1, cv2.LINE_AA)
                if lr.random() < 0.20:
                    by = int(round(cy + lr.choice([-1, 1]) * ry))
                    cv2.circle(target, (int(round(cx)), by), max(1, int(0.12 * space)), 255, -1)
            if abs(place) >= 6:
                _draw_ledgers(target, rows, space, cx, cy, 1.15 * space, line_thick)
            if lr.random() < 0.18:
                dy = float(lr.choice([-1.0, 1.0]) * space)
                _draw_hollow_head(target, cx, cy + dy, space, lr)

        elif cls_name == 'head_breve':
            if lr.random() < 0.45 and Path(NOTO_MUSIC).exists():
                _draw_font_glyph(target, UNICODE_GLYPHS['head_breve'], NOTO_MUSIC,
                                 int(round(lr.uniform(3.4, 4.4) * space)), cx, cy)
            else:
                rx = int(round(lr.uniform(0.74, 0.96) * space))
                ry = int(round(lr.uniform(0.44, 0.55) * space))
                cv2.ellipse(target, (int(round(cx)), int(round(cy))), (rx, ry), 0, 0, 360, 0, -1, cv2.LINE_AA)
                cv2.ellipse(target, (int(round(cx)), int(round(cy))),
                            (max(2, int(0.44 * rx)), max(2, int(0.65 * ry))),
                            20, 0, 360, 255, -1, cv2.LINE_AA)
                bar_h = int(round(lr.uniform(0.65, 0.95) * space))
                double_bar = lr.random() < 0.5
                for sgn in (-1, 1):
                    bx = int(round(cx + sgn * (rx + 0.14 * space)))
                    cv2.line(target, (bx, int(cy - bar_h)), (bx, int(cy + bar_h)), 0, stem_thick)
                    if double_bar:
                        bx2 = int(round(cx + sgn * (rx + 0.34 * space)))
                        cv2.line(target, (bx2, int(cy - bar_h)), (bx2, int(cy + bar_h)), 0, stem_thick)
            if abs(place) >= 6:
                _draw_ledgers(target, rows, space, cx, cy, 1.3 * space, line_thick)

        elif cls_name in ('rest_whole', 'rest_half'):
            rw = int(round(lr.uniform(0.88, 1.60) * space))
            rh = int(round(lr.uniform(0.36, 0.58) * space))
            x0, x1 = int(round(cx - rw / 2)), int(round(cx + rw / 2))
            if ledger_rest:
                wing = int(round(lr.uniform(0.28, 0.62) * space))
                ly = int(round(ledger_line_y))
                cv2.line(target, (x0 - wing, ly), (x1 + wing, ly), 0, line_thick)
                if cls_name == 'rest_whole':
                    cv2.rectangle(target, (x0, ly), (x1, ly + rh), 0, -1)
                else:
                    cv2.rectangle(target, (x0, ly - rh), (x1, ly), 0, -1)
            else:
                if cls_name == 'rest_whole':
                    y0 = int(round(rows[1]))
                    cv2.rectangle(target, (x0, y0), (x1, y0 + rh), 0, -1)
                else:
                    y1 = int(round(rows[2]))
                    cv2.rectangle(target, (x0, y1 - rh), (x1, y1), 0, -1)
            # Optional other-voice notehead far enough inside the staff.
            if lr.random() < 0.18:
                ny = rows[3] if cy < rows[2] else rows[1]
                if abs(ny - cy) >= 1.3 * space:
                    cv2.ellipse(target, (int(round(cx)), int(round(ny))),
                                (int(0.58 * space), int(0.42 * space)), -20, 0, 360, 0, -1, cv2.LINE_AA)

        elif cls_name == 'rest_quarter':
            roll = lr.random()
            if roll < 0.30 and Path(NOTO_MUSIC).exists():
                px = int(round(lr.uniform(3.4, 4.7) * space))
                sx = float(lr.uniform(0.55, 1.05))
                _draw_font_glyph(target, UNICODE_GLYPHS['rest_quarter'], NOTO_MUSIC, px, cx, cy,
                                 lr.uniform(-5, 5), scale_x=sx)
            elif roll < 0.68:
                _draw_slim_quarter_rest(target, cx, cy, space, lr, 'slim')
            elif roll < 0.92:
                _draw_slim_quarter_rest(target, cx, cy, space, lr, 'auto')
            else:
                _draw_cross_quarter_rest(target, cx, cy, space, lr)

        elif cls_name == 'rest_eighth':
            roll = lr.random()
            if roll < 0.35 and Path(NOTO_MUSIC).exists():
                px = int(round(lr.uniform(2.6, 4.4) * space))
                _draw_font_glyph(target, UNICODE_GLYPHS['rest_eighth'], NOTO_MUSIC, px, cx, cy,
                                 lr.uniform(-5, 5), scale_x=float(lr.uniform(0.8, 1.1)))
            elif roll < 0.72:
                _draw_procedural_eighth_rest(target, cx, cy, space, lr, compact=True, double=False)
            else:
                _draw_procedural_eighth_rest(target, cx, cy, space, lr, compact=False, double=False)

        elif cls_name == 'rest_16th':
            if lr.random() < 0.45 and Path(NOTO_MUSIC).exists():
                px = int(round(lr.uniform(3.2, 4.6) * space))
                _draw_font_glyph(target, UNICODE_GLYPHS['rest_16th'], NOTO_MUSIC, px, cx, cy, lr.uniform(-5, 5))
            else:
                _draw_procedural_eighth_rest(target, cx, cy, space, lr, compact=False, double=True)

        elif cls_name in ('acc_sharp', 'acc_flat', 'acc_natural'):
            if lr.random() < 0.62 and Path(NOTO_MUSIC).exists():
                lo, hi = (3.0, 4.4) if cls_name != 'acc_flat' else (3.2, 4.5)
                px = int(round(lr.uniform(lo, hi) * space))
                _draw_font_glyph(target, UNICODE_GLYPHS[cls_name], NOTO_MUSIC, px, cx, cy, lr.uniform(-5, 5))
            else:
                _draw_procedural_accidental(target, cls_name, cx, cy, space, lr)
            if lr.random() < 0.55:
                nx = int(round(cx + lr.uniform(1.10, 1.65) * space))
                cv2.ellipse(target, (nx, int(round(cy))), (int(0.58 * space), int(0.42 * space)),
                            -20, 0, 360, 0, -1, cv2.LINE_AA)

        elif cls_name in ('clef_G', 'clef_F', 'clef_C'):
            scale_map = {'clef_G': (3.5, 4.6), 'clef_F': (3.3, 4.4), 'clef_C': (3.5, 4.5)}
            lo, hi = scale_map[cls_name]
            px = int(round(lr.uniform(lo, hi) * space))
            _draw_font_glyph(target, UNICODE_GLYPHS[cls_name], NOTO_MUSIC, px, cx, cy, lr.uniform(-4, 4))
            if lr.random() < 0.5:
                bx = int(round(cx - lr.uniform(0.9, 1.4) * space))
                cv2.line(target, (bx, int(round(rows[0]))), (bx, int(round(rows[4]))), 0, stem_thick)

        elif cls_name == 'dot':
            r = max(2, int(round(lr.uniform(0.14, 0.24) * space)))
            cv2.circle(target, (int(round(cx)), int(round(cy))), r, 0, -1, cv2.LINE_AA)
            if lr.random() < 0.72:
                nx = int(round(cx - lr.uniform(0.85, 1.35) * space))
                if lr.random() < 0.35:
                    _draw_hollow_head(target, nx, cy, space, lr)
                else:
                    cv2.ellipse(target, (nx, int(round(cy))), (int(0.58 * space), int(0.42 * space)),
                                -20, 0, 360, 0, -1, cv2.LINE_AA)

        elif cls_name == 'dynamic':
            if lr.random() < 0.85 and ITALIC_FONTS:
                text = str(lr.choice(['p', 'pp', 'ppp', 'mp', 'mf', 'f', 'ff', 'fff', 'fp', 'sf', 'sfz', 'cresc.', 'dim.', 'rit.']))
                font = str(lr.choice(ITALIC_FONTS))
                px = int(round(lr.uniform(1.15, 2.25) * space))
                _draw_font_glyph(target, text, font, px, cx, cy, lr.uniform(-5, 5))
            else:
                # Hairpin crescendo / diminuendo apex.
                hw = int(round(lr.uniform(1.2, 2.0) * space))
                hh = int(round(lr.uniform(0.35, 0.65) * space))
                left_apex = lr.random() < 0.5
                ax = int(round(cx - hw / 2)) if left_apex else int(round(cx + hw / 2))
                ox = int(round(cx + hw / 2)) if left_apex else int(round(cx - hw / 2))
                cv2.line(target, (ax, int(cy)), (ox, int(cy - hh)), 0, stem_thick, cv2.LINE_AA)
                cv2.line(target, (ax, int(cy)), (ox, int(cy + hh)), 0, stem_thick, cv2.LINE_AA)

        elif cls_name == 'fermata':
            dome = lr.random() < 0.72
            if lr.random() < 0.35 and Path(NOTO_MUSIC).exists():
                glyph = '\U0001D110' if dome else '\U0001D111'
                px = int(round(lr.uniform(3.2, 4.5) * space))
                _draw_font_glyph(target, glyph, NOTO_MUSIC, px, cx, cy, lr.uniform(-4, 4))
            else:
                _draw_procedural_fermata(target, cx, cy, space, lr, dome=dome)
            # Frequently a notehead sits directly under/over a fermata.
            if lr.random() < 0.40:
                ny = cy + (1.35 * space if dome else -1.35 * space)
                _draw_filled_head(target, cx, ny, space, lr)

        elif cls_name == 'noise':
            kind = str(lr.choice([
                'blank', 'barline', 'double_bar', 'slur', 'beam', 'flag_loop_up',
                'flag_loop_down', 'down_stem_neck', 'offcenter_head', 'speck', 'letter', 'time_digit',
            ]))
            if kind == 'barline':
                cv2.line(target, (int(cx), int(rows[0])), (int(cx), int(rows[4])), 0, max(1, int(0.14 * space)))
            elif kind == 'double_bar':
                cv2.line(target, (int(cx - 0.18 * space), int(rows[0])), (int(cx - 0.18 * space), int(rows[4])), 0, stem_thick)
                cv2.line(target, (int(cx + 0.22 * space), int(rows[0])), (int(cx + 0.22 * space), int(rows[4])), 0, max(2, int(0.32 * space)))
            elif kind == 'slur':
                sign = lr.choice([-1, 1])
                cv2.ellipse(target, (int(cx), int(cy + sign * 0.8 * space)),
                            (int(1.7 * space), int(0.75 * space)), 0,
                            190 if sign > 0 else 10, 350 if sign > 0 else 170,
                            0, max(1, int(0.16 * space)), cv2.LINE_AA)
            elif kind == 'beam':
                slope = float(lr.uniform(-0.22, 0.22))
                y_l = int(cy - 1.5 * space * slope)
                y_r = int(cy + 1.5 * space * slope)
                pts = np.array([
                    [int(cx - 1.5 * space), y_l - beam_thick // 2],
                    [int(cx + 1.5 * space), y_r - beam_thick // 2],
                    [int(cx + 1.5 * space), y_r + beam_thick // 2],
                    [int(cx - 1.5 * space), y_l + beam_thick // 2],
                ], np.int32)
                cv2.fillPoly(target, [pts], 0)
            elif kind in ('flag_loop_up', 'flag_loop_down'):
                sx = int(round(cx - 0.25 * space))
                cv2.line(target, (sx, int(cy - 1.6 * space)), (sx, int(cy + 1.6 * space)), 0, stem_thick)
                cv2.ellipse(target, (int(cx + 0.20 * space), int(cy)),
                            (int(0.45 * space), int(0.72 * space)),
                            10 if kind == 'flag_loop_up' else -10, -90, 90, 0,
                            max(2, int(0.22 * space)), cv2.LINE_AA)
            elif kind == 'down_stem_neck':
                # Down-stemmed note where crop centers on stem+flag below the head (classic eighth-rest FP).
                hy = cy - float(lr.uniform(1.05, 1.55) * space)
                hx = cx + float(lr.uniform(0.35, 0.70) * space)
                cv2.ellipse(target, (int(hx), int(hy)), (int(0.58 * space), int(0.42 * space)), -20, 0, 360, 0, -1, cv2.LINE_AA)
                sx = int(round(hx - 0.56 * space))
                cv2.line(target, (sx, int(hy)), (sx, int(hy + 3.2 * space)), 0, stem_thick)
                if lr.random() < 0.65:
                    pts = np.array([
                        [sx, int(hy + 3.1 * space)],
                        [int(sx + 0.75 * space), int(hy + 2.4 * space)],
                        [int(sx + 0.85 * space), int(hy + 1.6 * space)],
                    ], np.int32)
                    cv2.polylines(target, [pts], False, 0, max(2, int(0.22 * space)), cv2.LINE_AA)
            elif kind == 'offcenter_head':
                ang = float(lr.uniform(0, 2 * np.pi))
                dist = float(lr.uniform(1.10, 1.65) * space)
                hx, hy = cx + dist * np.cos(ang), cy + dist * np.sin(ang)
                _draw_filled_head(target, hx, hy, space, lr)
            elif kind == 'speck':
                for _ in range(int(lr.integers(1, 5))):
                    sx = int(cx + lr.uniform(-0.85, 0.85) * space)
                    sy = int(cy + lr.uniform(-0.85, 0.85) * space)
                    cv2.circle(target, (sx, sy), max(1, int(lr.uniform(0.06, 0.16) * space)), 0, -1)
            elif kind == 'letter' and SERIF_FONTS:
                ch = str(lr.choice(['a', 'e', 'o', 'n', 'r', 's', 't', 'b', 'd', 'h', 'g', 'y', 'O', 'S', 'G', 'M', 'Lord', 'the']))
                font = str(lr.choice(SERIF_FONTS))
                _draw_font_glyph(target, ch, font, int(round(lr.uniform(1.0, 1.9) * space)), cx, cy)
            elif kind == 'time_digit' and SERIF_FONTS:
                ch = str(lr.choice(['2', '3', '4', '6', '8', 'C']))
                font = str(lr.choice(SERIF_FONTS))
                _draw_font_glyph(target, ch, font, int(round(lr.uniform(1.8, 2.5) * space)), cx, cy)

    draw_symbol(bare_canvas)
    draw_symbol(canvas)
    # Draw five staff lines on full canvas only (not on bare_canvas).
    line_grey = int(rng.uniform(0, 75))
    for row in rows:
        ry = int(round(row))
        if 0 <= ry < side:
            cv2.line(canvas, (0, ry), (side - 1, ry), line_grey, line_thick)

    degraded, bare_mask, levels = _degrade_scan_levels(canvas, rng, bare=bare_canvas)
    assert bare_mask is not None
    return extract_patch(degraded, bare_mask, rows, space, cx, cy, levels=levels)


if __name__ == '__main__':
    rng = np.random.default_rng(42)
    for name in CLASSES:
        p = synthesize_sample(name, rng)
        assert p.shape == (3, PATCH_SIZE, PATCH_SIZE) and p.dtype == np.float32
    print(f'ok: synthesized all {len(CLASSES)} classes with shape (3, {PATCH_SIZE}, {PATCH_SIZE})')

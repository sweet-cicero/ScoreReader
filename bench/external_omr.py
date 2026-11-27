#!/usr/bin/env python3
"""Offline external OMR harness and head-to-head benchmark for ScoreReader.

Provides unified offline adapters and honest bench/eval_f1.py evaluation for:
  - ScoreReader (local NumPy + OpenCV pipeline, ~0.7 MB weights)
  - oemer (ONNX U-Net + SegNet end-to-end MusicXML OMR, 109.2 MB)
  - SMT++ full-page (PRAIG/smt-fp-grandstaff, 43.7 MB -> **kern -> MusicXML)
  - SMT++ system-cropped (antoniorv6/smt-grandstaff, 85.5 MB on ScoreReader systems.py
    crops, with automatic legacy decoder key remapping + end-ReLU so all 360 tensors work)
  - LEGATO (guangyangmusic/legato + Llama-3.2-11B-Vision encoder, 943.7M params, live
    bfloat16 offline inference -> ABC -> abc2xml.py -> MusicXML, with graceful gated skip
    fallback if vision encoder shard is absent)
  - Verovio (offline SVG rendering across 5 SMuFL fonts + **kern and ABC conversion)

Hard constraints:
  - 100% offline inference (HF_HUB_OFFLINE=1, local_files_only=True, zero cloud calls).
  - Never touches clean_holdout.json or any holdout score.
  - Never imports external OMR tools inside scorereader/.

Usage:
  PYTHONDONTWRITEBYTECODE=1 out/tools/omr-bench/verovio-venv/bin/python bench/external_omr.py \
      --out /tmp/scorereader_swarm/omr_eval/external_bench
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
from pathlib import Path
from typing import Any

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bench.eval_f1 import (
    align_notes,
    join_ties,
    match_staves,
    prf,
    read_musicxml,
    reader_tokens,
    score_case,
    split_by_clef,
    truth_tokens,
)
from bench.test_verovio_roundtrip import (
    build_roundtrip_suite,
    render_musicxml_to_png,
    run_scorereader_on_png,
    score_musicxml_pair,
)
from scorereader.cli import render as render_pdf_page
from scorereader.page import clean_page, flat_paper
from scorereader.staves import find_staves
from scorereader.systems import find_systems, lost_staves

BENCH_DIR = ROOT / 'out' / 'tools' / 'omr-bench'
VEROVIO_PY = BENCH_DIR / 'verovio-venv' / 'bin' / 'python'
OEMER_PY = BENCH_DIR / 'oemer-venv' / 'bin' / 'python'
OEMER_BIN = BENCH_DIR / 'oemer-venv' / 'bin' / 'oemer'
TRANSFORMERS_PY = BENCH_DIR / 'transformers-venv' / 'bin' / 'python'
SMT_REPO = BENCH_DIR / 'SMT'
LEGATO_REPO = BENCH_DIR / 'legato'
HF_CACHE = BENCH_DIR / 'hf-cache'

CLEAN_DEV_MANIFEST = ROOT / 'out' / 'eval' / 'clean_dev.json'
STRATIFIED_DEV_IDS = (
    'all-saints-troparion',
    'extra-come-bless',
    'pascha-christos-voskrese',
    'megalynarion-yaichkov',
    'transfiguration-troparion--s2',
)
VEROVIO_SATB_IDS = (
    'satb_hymn_4_4_sharps',
    'satb_hymn_3_4_flats',
)
ALL_TOOLS = ('scorereader', 'oemer', 'smt_fp', 'smt_sys', 'legato')

TOOL_META = {
    'scorereader': {'model_mb': 0.48, 'license': 'Project (local)', 'deps': 'NumPy + OpenCV'},
    'oemer': {'model_mb': 109.2, 'license': 'MIT', 'deps': 'ONNX Runtime + OpenCV + sklearn'},
    'smt_fp': {'model_mb': 43.7, 'license': 'MIT', 'deps': 'PyTorch + Transformers (PRAIG/smt-fp-grandstaff)'},
    'smt_sys': {'model_mb': 85.5, 'license': 'MIT', 'deps': 'PyTorch + Transformers (antoniorv6/smt-grandstaff)'},
    'legato': {'model_mb': 2110.0, 'license': 'MIT code / Llama-3.2-Vision license', 'deps': 'PyTorch + Transformers (943.7M params)'},
}


def _offline_env(extra: dict[str, str] | None = None, threads: int = 6) -> dict[str, str]:
    env = dict(os.environ)
    env.update({
        'PYTHONDONTWRITEBYTECODE': '1',
        'HF_HOME': str(HF_CACHE),
        'HF_HUB_OFFLINE': '1',
        'TRANSFORMERS_OFFLINE': '1',
        'MPLCONFIGDIR': '/tmp/scorereader_swarm/omr_eval/mpl',
        'OMP_WAIT_POLICY': 'PASSIVE',
        'GOMP_SPINCOUNT': '0',
        'OMP_NUM_THREADS': str(threads),
        'OPENBLAS_NUM_THREADS': str(threads),
        'MKL_NUM_THREADS': str(threads),
    })
    if extra:
        env.update(extra)
    Path(env['MPLCONFIGDIR']).mkdir(parents=True, exist_ok=True)
    return env


# ---------------------------------------------------------------------------
# PDF/PNG preparation & ScoreReader systems.py cropping
# ---------------------------------------------------------------------------

def render_pdf_page_rgb(pdf_path: Path, page: int, out_png: Path) -> Path:
    """Renders one PDF page at 300 DPI and saves a crisp 3-channel RGB PNG."""
    out_png.parent.mkdir(parents=True, exist_ok=True)
    stem = out_png.with_suffix('')
    raw_stem = out_png.parent / f'.raw_{stem.name}'
    render_pdf_page(pdf_path, page, raw_stem)
    raw_png = Path(str(raw_stem) + '.png')
    grey = cv2.imread(str(raw_png), cv2.IMREAD_GRAYSCALE)
    if raw_png.exists():
        raw_png.unlink()
    if grey is None:
        raise RuntimeError(f'Failed to render PDF page {page} of {pdf_path}')
    rgb = cv2.cvtColor(grey, cv2.COLOR_GRAY2BGR)
    cv2.imwrite(str(out_png), rgb)
    return out_png


def ensure_rgb_png(src_png: Path, dst_png: Path) -> Path:
    """Ensures an RGB 3-channel PNG copy exists at dst_png."""
    img = cv2.imread(str(src_png), cv2.IMREAD_COLOR)
    if img is None:
        raise RuntimeError(f'Cannot read image: {src_png}')
    dst_png.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(dst_png), img)
    return dst_png


def crop_systems_with_scorereader(png_path: Path, out_dir: Path, prefix: str) -> list[dict[str, Any]]:
    """Uses ScoreReader's staves.py + systems.py + page.py to extract de-skewed per-system PNG crops."""
    grey = cv2.imread(str(png_path), cv2.IMREAD_GRAYSCALE)
    if grey is None:
        return []
    grey = flat_paper(grey)
    staves = find_staves(grey)
    if not staves:
        return []
    systems = find_systems(grey, staves)
    staves, systems = lost_staves(grey, staves, systems)
    clean, places = clean_page(grey, staves, systems)
    out_dir.mkdir(parents=True, exist_ok=True)
    crops: list[dict[str, Any]] = []
    h, w = clean.shape
    for idx, pl in enumerate(places):
        lines = pl['lines']
        xs = pl['x']
        if not lines:
            continue
        sp = float(np.median(np.diff(lines[0]))) if len(lines[0]) >= 2 else 20.0
        y0 = max(0, int(round(lines[0][0] - 2.6 * sp)))
        y1 = min(h, int(round(lines[-1][-1] + 2.8 * sp)))
        x0 = max(0, int(round(min(pair[0] for pair in xs) - 2.2 * sp)))
        x1 = min(w, int(round(max(pair[1] for pair in xs) + 1.2 * sp)))
        if y1 <= y0 + 20 or x1 <= x0 + 40:
            continue
        crop = clean[y0:y1, x0:x1]
        cpath = out_dir / f'{prefix}_sys{idx:02d}.png'
        cv2.imwrite(str(cpath), crop)
        crops.append({
            'index': idx,
            'path': str(cpath),
            'num_staves': len(lines),
            'width': int(crop.shape[1]),
            'height': int(crop.shape[0]),
        })
    return crops


# ---------------------------------------------------------------------------
# Robust **kern -> MusicXML and ABC -> MusicXML conversion
# ---------------------------------------------------------------------------

_KERN_PITCH_RE = re.compile(r'([A-Ga-g]+)(##|--|#|-|n)?')
_KERN_DUR_RE = re.compile(r'^(\d+)(\.*)')


def normalize_smt_kern(raw_kern: str) -> str:
    """Normalizes SMT bekern/ekern/kern output into standard multi-spine Humdrum **kern text."""
    text = raw_kern.replace('·', '').replace('@', '').replace('\r\n', '\n')
    raw_lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith('!!')]
    if not raw_lines:
        return ''

    col_counts = Counter(len(ln.split('\t')) for ln in raw_lines if not ln.startswith('**') and not ln.startswith('*-'))
    n_spines = col_counts.most_common(1)[0][0] if col_counts else 2
    n_spines = max(1, min(4, n_spines))

    out: list[str] = ['\t'.join(['**kern'] * n_spines)]
    for ln in raw_lines:
        if ln.startswith('**') or ln.startswith('*-'):
            continue
        cols = ln.split('\t')
        if any(c in ('*^', '*v', '*+') for c in cols):
            continue
        if len(cols) < n_spines:
            pad = '=' if ln.startswith('=') else ('*' if ln.startswith('*') else '.')
            cols.extend([pad] * (n_spines - len(cols)))
        elif len(cols) > n_spines:
            cols = cols[:n_spines]
        cleaned = [c.strip() or '.' for c in cols]
        out.append('\t'.join(cleaned))

    out.append('\t'.join(['*-'] * n_spines))
    return '\n'.join(out) + '\n'


def _kern_pitch_to_step_oct_alter(tok: str) -> tuple[str, int, int] | None:
    m = _KERN_PITCH_RE.search(tok)
    if not m:
        return None
    letters, acc = m.group(1), m.group(2) or ''
    ch = letters[0]
    if ch.isupper():
        octave = 4 - len(letters)
        step = ch
    else:
        octave = 3 + len(letters)
        step = ch.upper()
    alter = {'##': 2, '#': 1, '-': -1, '--': -2, 'n': 0, '': 0}.get(acc, 0)
    return step, max(0, min(8, octave)), alter


def _fallback_kern_to_musicxml(kern_text: str, title: str = 'smt') -> str:
    """Resilient pure-Python **kern -> MusicXML converter when strict Humdrum parsing fails."""
    lines = [ln for ln in kern_text.splitlines() if ln.strip()]
    if not lines:
        return ''
    n_spines = max(1, len(lines[0].split('\t')))
    spine_order = list(reversed(range(n_spines)))
    divisions = 24

    spine_measures: list[list[dict[str, Any]]] = [[{'events': [], 'clef': None, 'time': None, 'fifths': None}] for _ in range(n_spines)]
    active_clef = ['F' if i == 0 and n_spines >= 2 else 'G' for i in range(n_spines)]
    active_time: list[tuple[int, int] | None] = [None] * n_spines
    active_key: list[int | None] = [None] * n_spines

    for ln in lines[1:]:
        if ln.startswith('*-') or ln.startswith('**'):
            continue
        cols = ln.split('\t')
        if len(cols) < n_spines:
            cols += ['.'] * (n_spines - len(cols))
        if cols[0].startswith('='):
            for s in range(n_spines):
                if spine_measures[s][-1]['events']:
                    spine_measures[s].append({'events': [], 'clef': None, 'time': None, 'fifths': None})
            continue
        if cols[0].startswith('*'):
            for s in range(n_spines):
                tok = cols[s].strip()
                if tok.startswith('*clefG'):
                    active_clef[s] = 'G'
                    spine_measures[s][-1]['clef'] = ('G', 2)
                elif tok.startswith('*clefF'):
                    active_clef[s] = 'F'
                    spine_measures[s][-1]['clef'] = ('F', 4)
                elif tok.startswith('*M') and '/' in tok:
                    mm = re.match(r'\*M(\d+)/(\d+)', tok)
                    if mm:
                        active_time[s] = (int(mm.group(1)), int(mm.group(2)))
                        spine_measures[s][-1]['time'] = active_time[s]
                elif tok.startswith('*k['):
                    inner = tok[3:].rstrip(']')
                    fifths = inner.count('#') if inner.count('#') else -inner.count('-')
                    active_key[s] = fifths
                    spine_measures[s][-1]['fifths'] = fifths
            continue

        for s in range(n_spines):
            cell = cols[s].strip()
            if not cell or cell == '.' or cell.startswith('!'):
                continue
            chord_notes = []
            for st in (t for t in cell.split(' ') if t and t != '.'):
                tie_start = '[' in st
                tie_stop = ']' in st
                clean = re.sub(r'[()\[\]{}LJkK<>xyXzZ;:~^\'/\\]', '', st)
                dm = _KERN_DUR_RE.match(clean)
                if not dm:
                    continue
                recip = int(dm.group(1))
                dots = len(dm.group(2))
                if recip <= 0 or recip > 64:
                    continue
                q_len = Fraction(4, recip)
                if dots == 1:
                    q_len *= Fraction(3, 2)
                elif dots == 2:
                    q_len *= Fraction(7, 4)
                dur_ticks = max(1, int(round(float(q_len) * divisions)))
                rest_body = clean[dm.end():]
                if 'r' in rest_body:
                    chord_notes.append({'rest': True, 'dur': dur_ticks})
                else:
                    parsed_p = _kern_pitch_to_step_oct_alter(rest_body)
                    if parsed_p:
                        step, octv, alt = parsed_p
                        chord_notes.append({
                            'rest': False, 'step': step, 'octave': octv, 'alter': alt,
                            'dur': dur_ticks, 'tie_start': tie_start, 'tie_stop': tie_stop,
                        })
            if chord_notes:
                spine_measures[s][-1]['events'].append(chord_notes)

    plist, pbody = [], []
    for p_idx, s in enumerate(spine_order, 1):
        plist.append(f'<score-part id="P{p_idx}"><part-name>Part {p_idx}</part-name></score-part>')
        m_xml = []
        for m_i, m in enumerate(spine_measures[s], 1):
            elems, attrs = [], []
            if m_i == 1:
                attrs.append(f'<divisions>{divisions}</divisions>')
                kf = m['fifths'] if m['fifths'] is not None else (active_key[s] or 0)
                attrs.append(f'<key><fifths>{kf}</fifths></key>')
                ts = m['time'] or active_time[s]
                if ts:
                    attrs.append(f'<time><beats>{ts[0]}</beats><beat-type>{ts[1]}</beat-type></time>')
                cl = m['clef'] or (active_clef[s], 2 if active_clef[s] == 'G' else 4)
                attrs.append(f'<clef><sign>{cl[0]}</sign><line>{cl[1]}</line></clef>')
            else:
                if m['time']:
                    attrs.append(f'<time><beats>{m["time"][0]}</beats><beat-type>{m["time"][1]}</beat-type></time>')
                if m['clef']:
                    attrs.append(f'<clef><sign>{m["clef"][0]}</sign><line>{m["clef"][1]}</line></clef>')
            if attrs:
                elems.append('<attributes>' + ''.join(attrs) + '</attributes>')
            for ev in m['events']:
                for ci, item in enumerate(ev):
                    if item['rest']:
                        elems.append(f'<note><rest/><duration>{item["dur"]}</duration><voice>1</voice></note>')
                    else:
                        ch_tag = '<chord/>' if ci > 0 else ''
                        alt_tag = f'<alter>{item["alter"]}</alter>' if item['alter'] != 0 else ''
                        t_tags = ('<tie type="start"/>' if item['tie_start'] else '') + ('<tie type="stop"/>' if item['tie_stop'] else '')
                        elems.append(
                            f'<note>{ch_tag}<pitch><step>{item["step"]}</step>{alt_tag}<octave>{item["octave"]}</octave></pitch>'
                            f'<duration>{item["dur"]}</duration>{t_tags}<voice>1</voice></note>'
                        )
            m_xml.append(f'<measure number="{m_i}">{"".join(elems)}</measure>')
        pbody.append(f'<part id="P{p_idx}">{"".join(m_xml)}</part>')
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<score-partwise version="3.1">'
        f'<work><work-title>{title}</work-title></work>'
        f'<part-list>{"".join(plist)}</part-list>'
        f'{"".join(pbody)}'
        '</score-partwise>'
    )


def kern_to_musicxml(raw_kern: str, out_xml: Path, title: str = 'smt') -> tuple[bool, str]:
    """Converts SMT **kern text to MusicXML using music21 with a resilient fallback parser."""
    norm = normalize_smt_kern(raw_kern)
    out_xml.parent.mkdir(parents=True, exist_ok=True)
    if not norm:
        return False, 'empty_kern'
    try:
        import music21  # noqa: PLC0415
        score = music21.converter.parseData(norm, format='humdrum')
        score.write('musicxml', fp=str(out_xml))
        parsed = read_musicxml(out_xml)
        if sum(len(s) for s in parsed['notes']) > 0:
            return True, 'music21'
    except Exception:
        pass
    xml_text = _fallback_kern_to_musicxml(norm, title=title)
    if xml_text:
        out_xml.write_text(xml_text, encoding='utf-8')
        try:
            read_musicxml(out_xml)
            return True, 'fallback'
        except Exception as exc:
            return False, f'fallback_error: {exc}'
    return False, 'conversion_failed'


def clean_legato_abc(abc_text: str) -> str:
    """Cleans raw LEGATO ABC predictions so abc2xml.py converts them reliably without MuseScore."""
    text = abc_text.replace('<|text|>', 'text').replace('\r\n', '\n')
    text = re.sub(r'nm=text\b', 'nm="Part"', text)
    text = re.sub(r'snm=text\b', '', text)
    # Remove lyric lines AND all blank lines (a blank line terminates an ABC tune in abc2xml.py!).
    kept_lines = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s or s.startswith('w:') or s.startswith('W:'):
            continue
        kept_lines.append(ln)
    text = '\n'.join(kept_lines)
    # Balance brackets on %%score line
    m = re.search(r'^(%%score )(.*)$', text, flags=re.MULTILINE)
    if m:
        pair = {'(': ')', '[': ']', '{': '}'}
        stack = []
        for ch in m.group(2):
            if ch in pair:
                stack.append(ch)
            elif ch in pair.values() and stack and pair[stack[-1]] == ch:
                stack.pop()
        fixed = m.group(2) + ''.join(pair[c] for c in reversed(stack))
        text = text[:m.start()] + m.group(1) + fixed + text[m.end():]
    if not text.strip().startswith('X:'):
        text = 'X:1\n' + text
    return text.strip() + '\n'


def abc_to_musicxml(abc_text: str, out_xml: Path) -> tuple[bool, str]:
    """Converts LEGATO ABC notation to MusicXML using legato/utils/abc2xml.py."""
    cleaned = clean_legato_abc(abc_text)
    out_xml.parent.mkdir(parents=True, exist_ok=True)
    abc_path = out_xml.with_suffix('.clean.abc')
    abc_path.write_text(cleaned, encoding='utf-8')
    abc2xml = LEGATO_REPO / 'utils' / 'abc2xml.py'
    proc = subprocess.run(
        [str(VEROVIO_PY), str(abc2xml), str(abc_path)],
        env=_offline_env(threads=2),
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode == 0 and '<score-partwise' in proc.stdout:
        out_xml.write_text(proc.stdout, encoding='utf-8')
        try:
            read_musicxml(out_xml)
            return True, 'abc2xml'
        except Exception as exc:
            return False, f'xml_parse_err: {exc}'
    tail = (proc.stderr or '').strip().splitlines()[-2:]
    return False, ' | '.join(tail) or 'abc2xml_failed'


# ---------------------------------------------------------------------------
# Tool Adapters: oemer, SMT++ full-page, SMT++ system-cropped, LEGATO, Verovio
# ---------------------------------------------------------------------------

_OEMER_WORKER_CODE = r"""
import os, sys, types, warnings
from argparse import Namespace
from pathlib import Path

warnings.filterwarnings('ignore')

site_pkgs = next(p for p in sys.path if p.endswith('site-packages'))
ort_dir = Path(site_pkgs) / 'onnxruntime'
pkg = types.ModuleType('onnxruntime')
pkg.__path__ = [str(ort_dir)]
sys.modules['onnxruntime'] = pkg
capi = types.ModuleType('onnxruntime.capi')
capi.__path__ = [str(ort_dir / 'capi')]
sys.modules['onnxruntime.capi'] = capi
import onnxruntime.capi._pybind_state as _ps
if not hasattr(_ps, 'set_default_logger_callback'):
    _ps.set_default_logger_callback = lambda *a, **kw: None
import onnxruntime.capi.onnxruntime_inference_collection as _ic

class _CompatInferenceSession(_ic.InferenceSession):
    def __init__(self, path_or_bytes, sess_options=None, providers=None, **kwargs):
        if sess_options is None:
            sess_options = _ps.SessionOptions()
            sess_options.graph_optimization_level = _ps.GraphOptimizationLevel.ORT_ENABLE_EXTENDED
            sess_options.intra_op_num_threads = int(os.environ.get('OMP_NUM_THREADS', '6'))
            sess_options.inter_op_num_threads = 1
        super().__init__(path_or_bytes, sess_options=sess_options, providers=['CPUExecutionProvider'], **kwargs)

pkg.InferenceSession = _CompatInferenceSession
pkg.SessionOptions = _ps.SessionOptions
pkg.GraphOptimizationLevel = _ps.GraphOptimizationLevel
pkg.get_available_providers = lambda: ['CPUExecutionProvider']

import cv2 as _cv2
import numpy as _np

# OpenCV 5.1 rejects uint64/int64 contours in drawContours/contourArea/fillPoly and numpy scalars in putText/rectangle.
_orig_drawContours = _cv2.drawContours
def _compat_drawContours(image, contours, contourIdx, color, *args, **kwargs):
    c32 = [_np.asarray(c, dtype=_np.int32) for c in contours]
    return _orig_drawContours(image, c32, contourIdx, color, *args, **kwargs)
_cv2.drawContours = _compat_drawContours

_orig_contourArea = _cv2.contourArea
def _compat_contourArea(contour, *args, **kwargs):
    return _orig_contourArea(_np.asarray(contour, dtype=_np.int32), *args, **kwargs)
_cv2.contourArea = _compat_contourArea

_orig_fillPoly = _cv2.fillPoly
def _compat_fillPoly(img, pts, color, *args, **kwargs):
    p32 = [_np.asarray(p, dtype=_np.int32) for p in pts]
    return _orig_fillPoly(img, p32, color, *args, **kwargs)
_cv2.fillPoly = _compat_fillPoly

_orig_putText = _cv2.putText
def _compat_putText(img, text, org, *args, **kwargs):
    return _orig_putText(img, text, (int(org[0]), int(org[1])), *args, **kwargs)
_cv2.putText = _compat_putText

_orig_rectangle = _cv2.rectangle
def _compat_rectangle(img, pt1, pt2, color, *args, **kwargs):
    return _orig_rectangle(img, (int(pt1[0]), int(pt1[1])), (int(pt2[0]), int(pt2[1])), color, *args, **kwargs)
_cv2.rectangle = _compat_rectangle

import oemer
import oemer.bbox as _obbox

# OpenCV >=4.12 returns HoughLinesP as (N, 4) instead of (N, 1, 4); patch BEFORE importing oemer.ete!
def _compat_find_lines(data, min_len=10, max_gap=20):
    lines = _cv2.HoughLinesP(data.astype(_np.uint8), 1, _np.pi / 180, 50, None, min_len, max_gap)
    out = []
    if lines is not None:
        arr = _np.asarray(lines).reshape(-1, 4)
        for x0, y0, x1, y1 in arr:
            tx, bx = (int(x0), int(x1)) if x0 < x1 else (int(x1), int(x0))
            ty, by = (int(y0), int(y1)) if y0 < y1 else (int(y1), int(y0))
            out.append((tx, ty, bx, by))
    return out

_obbox.find_lines = _compat_find_lines
_orig_merge_bbox = _obbox.merge_nearby_bbox
def _compat_merge_nearby_bbox(bboxes, distance, **kwargs):
    if len(bboxes) < 2:
        return list(bboxes)
    return _orig_merge_bbox(bboxes, distance, **kwargs)
_obbox.merge_nearby_bbox = _compat_merge_nearby_bbox
import oemer.ete as ete

orig_mod = Path(oemer.MODULE_PATH)
mirror = Path('/tmp/scorereader_swarm/omr_eval/oemer_mod')
for sub, src_onnx in (('unet_big', '1st_model.onnx'), ('seg_net', '2nd_model.onnx')):
    dst = mirror / 'checkpoints' / sub
    dst.mkdir(parents=True, exist_ok=True)
    src_dir = orig_mod / 'checkpoints' / sub
    for fname in ('arch.json', 'metadata.pkl'):
        link = dst / fname
        if not link.exists():
            os.symlink(src_dir / fname, link)
    onnx_link = dst / 'model.onnx'
    if not onnx_link.exists():
        os.symlink(src_dir / src_onnx, onnx_link)
for item in orig_mod.iterdir():
    if item.name == 'checkpoints':
        continue
    link = mirror / item.name
    if not link.exists():
        os.symlink(item, link)

oemer.MODULE_PATH = str(mirror)
ete.MODULE_PATH = str(mirror)

img_path, out_dir = sys.argv[1], sys.argv[2]
ete.clear_data()
args = Namespace(img_path=img_path, output_path=out_dir, use_tf=False, save_cache=True, without_deskew=True)
mxl_path = ete.extract(args)
print('OEMER_OUT:', mxl_path)
"""


def run_oemer_on_png(
    png_path: Path,
    out_xml: Path,
    timeout: int = 900,
    threads: int = 6,
    reuse_cache: bool = False,
) -> dict[str, Any]:
    """Runs offline oemer ONNX inference on one RGB PNG and writes out_xml."""
    t0 = time.time()
    work = out_xml.parent / f'_oemer_{out_xml.stem}'
    if work.exists() and not reuse_cache:
        shutil.rmtree(work)
    work.mkdir(parents=True, exist_ok=True)
    rgb_in = ensure_rgb_png(png_path, work / f'{out_xml.stem}.png')
    worker_py = work / '_oemer_worker.py'
    worker_py.write_text(_OEMER_WORKER_CODE, encoding='utf-8')
    cmd = [str(OEMER_PY), str(worker_py), str(rgb_in), str(work)]
    try:
        proc = subprocess.run(cmd, env=_offline_env(threads=threads), capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {'ok': False, 'seconds': round(time.time() - t0, 2), 'xml': None, 'err': f'timeout>{timeout}s'}
    elapsed = time.time() - t0
    produced = work / f'{out_xml.stem}.musicxml'
    if proc.returncode == 0 and produced.exists():
        shutil.copy2(produced, out_xml)
        return {'ok': True, 'seconds': round(elapsed, 2), 'xml': str(out_xml), 'err': ''}
    tail = (proc.stderr or proc.stdout or '').strip().splitlines()[-4:]
    return {'ok': False, 'seconds': round(elapsed, 2), 'xml': None, 'err': ' | '.join(tail)}


_SMT_WORKER_CODE = r"""
import json, os, sys, time, glob
from pathlib import Path
import cv2
import numpy as np
import torch
import torch.nn.functional as F
from safetensors import safe_open
from torchvision import transforms

sys.path.insert(0, os.environ['SMT_REPO'])
from smt_model import SMTConfig, SMTModelForCausalLM

_IMG_TO_TENSOR = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Grayscale(),
    transforms.ToTensor(),
])

def convert_img_to_tensor(image):
    return _IMG_TO_TENSOR(image)

def load_smt_offline(model_id: str):
    slug = 'models--' + model_id.replace('/', '--')
    snaps = sorted(glob.glob(os.path.join(os.environ['HF_HOME'], 'hub', slug, 'snapshots', '*')))
    if not snaps:
        raise FileNotFoundError(f'Offline snapshot not found for {model_id}')
    snap = Path(snaps[-1])
    cfg = SMTConfig.from_pretrained(str(snap), local_files_only=True)
    model = SMTModelForCausalLM(cfg)
    raw_sd = {}
    with safe_open(str(snap / 'model.safetensors'), framework='pt') as f:
        for k in f.keys():
            raw_sd[k] = f.get_tensor(k)

    # Detect legacy antoniorv6/smt-grandstaff decoder (uses DAN Conv1d out_layer + end_relu).
    is_legacy = 'decoder.out_layer.weight' in raw_sd
    remapped = {}
    for k, v in raw_sd.items():
        nk = k
        if '.cross_attention.' in nk:
            nk = nk.replace('.cross_attention.', '.cross_attn.')
        if '.input_attention.' in nk:
            nk = nk.replace('.input_attention.', '.self_attn.')
        nk = nk.replace('.lq.', '.q_proj.').replace('.lk.', '.k_proj.').replace('.lv.', '.v_proj.')
        nk = nk.replace('.ffNet.', '.ffn.')
        nk = nk.replace('.norm1.', '.norm_layers.0.').replace('.norm2.', '.norm_layers.1.').replace('.norm3.', '.norm_layers.2.')
        if nk == 'decoder.out_layer.weight':
            nk = 'decoder.vocab_projection.weight'
            if v.ndim == 3 and v.shape[-1] == 1:
                v = v.squeeze(-1)
        elif nk == 'decoder.out_layer.bias':
            nk = 'decoder.vocab_projection.bias'
        remapped[nk] = v

    missing, unexpected = model.load_state_dict(remapped, strict=False)
    model.eval()
    return model, missing, unexpected, is_legacy

@torch.no_grad()
def predict_fast(model, tensor, max_tokens: int, use_end_relu: bool):
    i2w = model.i2w
    w2i = model.w2i
    bos = int(w2i['<bos>'])
    seq = torch.tensor([[bos]], dtype=torch.long)
    enc = model.forward_encoder(tensor)
    tokens = []
    limit = min(int(model.maxlen) - 2, max_tokens)
    for _ in range(limit):
        out = model.forward_decoder(encoder_output=enc, last_predictions=seq)
        if use_end_relu:
            logits = model.decoder.vocab_projection(F.relu(out.hidden_states[:, -1, :]))
        else:
            logits = out.logits[:, -1, :]
        nxt = int(torch.argmax(logits, dim=-1).item())
        seq = torch.cat([seq, torch.tensor([[nxt]], dtype=torch.long)], dim=1)
        tok = i2w.get(str(nxt), i2w.get(nxt, ''))
        if tok == '<eos>':
            break
        tokens.append(tok)
        # Early-stop degenerate repetition loops of any short period 1..20 (e.g. '. <t> 4 r <b>')
        n_tok = len(tokens)
        looped = False
        for per in range(1, 21):
            if n_tok >= 4 * per and tokens[-per:] == tokens[-2 * per:-per] == tokens[-3 * per:-2 * per] == tokens[-4 * per:-3 * per]:
                tokens = tokens[:-3 * per]
                looped = True
                break
        if looped:
            break
    return tokens

spec = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
torch.set_num_threads(int(spec.get('threads', 6)))
model_id = spec['model_id']
mode = spec['mode']
max_tokens = int(spec.get('max_tokens', 700 if mode == 'fp' else 240))

t_load = time.time()
model, missing, unexpected, is_legacy = load_smt_offline(model_id)
load_sec = time.time() - t_load

results = []
for item in spec['jobs']:
    t0 = time.time()
    img_paths = item['images']
    krn_parts = []
    tok_count = 0
    for ip in img_paths:
        img = cv2.imread(ip)
        if img is None:
            continue
        h, w = img.shape[:2]
        if mode == 'fp':
            target_w = min(int(model.config.maxw), max(768, int(round(w * 0.45))))
            scale = min(target_w / max(1, w), (int(model.config.maxh) - 16) / max(1, h))
            nh, nw = max(64, int(round(h * scale))), max(64, int(round(w * scale)))
            img = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)
        else:
            target_h = min(int(model.config.maxh), 256)
            scale = min(target_h / max(1, h), (int(model.config.maxw) - 16) / max(1, w))
            nh = max(64, min(int(model.config.maxh), int(round(h * scale))))
            nw = max(64, min(int(model.config.maxw), int(round(w * scale))))
            img = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)
        ten = convert_img_to_tensor(img).unsqueeze(0)
        toks = predict_fast(model, ten, max_tokens=max_tokens, use_end_relu=is_legacy)
        tok_count += len(toks)
        krn = ''.join(toks).replace('<b>', '\n').replace('<s>', ' ').replace('<t>', '\t')
        krn_parts.append(krn)
    merged = '\n=\t=\n'.join(p.strip() for p in krn_parts if p.strip())
    Path(item['kern_out']).write_text(merged, encoding='utf-8')
    results.append({
        'id': item['id'],
        'seconds': round(time.time() - t0, 2),
        'tokens': tok_count,
        'systems': len(img_paths),
        'kern_out': item['kern_out'],
    })

Path(spec['result_json']).write_text(json.dumps({
    'model_id': model_id,
    'mode': mode,
    'is_legacy': is_legacy,
    'load_sec': round(load_sec, 2),
    'missing_keys': len(missing),
    'unexpected_keys': len(unexpected),
    'results': results,
}, indent=2), encoding='utf-8')
"""


def run_smt_batch(
    model_id: str,
    mode: str,
    jobs: list[dict[str, Any]],
    work_dir: Path,
    max_tokens: int | None = None,
    threads: int = 6,
) -> dict[str, Any]:
    """Runs offline SMT++ inference over a batch of full-page or system-cropped jobs in one model load."""
    work_dir.mkdir(parents=True, exist_ok=True)
    spec_path = work_dir / f'smt_{mode}_spec.json'
    res_path = work_dir / f'smt_{mode}_result.json'
    worker_py = work_dir / '_smt_worker.py'
    worker_py.write_text(_SMT_WORKER_CODE, encoding='utf-8')
    spec = {
        'model_id': model_id,
        'mode': mode,
        'max_tokens': max_tokens or (700 if mode == 'fp' else 240),
        'threads': threads,
        'jobs': jobs,
        'result_json': str(res_path),
    }
    spec_path.write_text(json.dumps(spec, indent=2), encoding='utf-8')
    env = _offline_env({'SMT_REPO': str(SMT_REPO)}, threads=threads)
    proc = subprocess.run([str(TRANSFORMERS_PY), str(worker_py), str(spec_path)], env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f'SMT worker failed ({model_id}): {proc.stderr[-1200:]}')
    data = json.loads(res_path.read_text(encoding='utf-8'))
    for item, res in zip(jobs, data['results']):
        krn_text = Path(res['kern_out']).read_text(encoding='utf-8')
        ok, conv_mode = kern_to_musicxml(krn_text, Path(item['xml_out']), title=item['id'])
        res['xml_ok'] = ok
        res['xml_converter'] = conv_mode
        res['xml_out'] = item['xml_out']
    return data


_LEGATO_WORKER_CODE = r"""
import json, os, sys, time
from pathlib import Path
from PIL import Image
import torch
from transformers import AutoProcessor, GenerationConfig

sys.path.insert(0, os.environ['LEGATO_REPO'])
from legato.models import LegatoModel

spec = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
threads = int(spec.get('threads', 8))
torch.set_num_threads(threads)
model_id = spec.get('model_id', 'guangyangmusic/legato')
max_new_tokens = int(spec.get('max_new_tokens', 700))
num_beams = int(spec.get('num_beams', 1))

t_load = time.time()
try:
    model = LegatoModel.from_pretrained(model_id, local_files_only=True, torch_dtype=torch.bfloat16)
    model.eval()
    processor = AutoProcessor.from_pretrained(model_id, local_files_only=True)
    params = sum(p.numel() for p in model.parameters())
except Exception as exc:
    Path(spec['result_json']).write_text(json.dumps({
        'status': 'gated_skipped',
        'error': f'{type(exc).__name__}: {exc}',
        'results': [],
    }, indent=2), encoding='utf-8')
    sys.exit(0)
load_sec = time.time() - t_load

gcfg = GenerationConfig(
    max_new_tokens=max_new_tokens,
    num_beams=num_beams,
    do_sample=False,
    repetition_penalty=1.05,
)

results = []
for item in spec['jobs']:
    t0 = time.time()
    img = Image.open(item['image']).convert('RGB')
    inputs = processor(images=[img], truncation=True, return_tensors='pt')
    if 'pixel_values' in inputs:
        inputs['pixel_values'] = inputs['pixel_values'].to(torch.bfloat16)
    with torch.no_grad():
        out = model.generate(**inputs, generation_config=gcfg, use_model_defaults=False)
    abc = processor.batch_decode(out, skip_special_tokens=True)[0]
    Path(item['abc_out']).write_text(abc, encoding='utf-8')
    sec = round(time.time() - t0, 2)
    print(f"  legato {item['id']:34s}: {sec:6.2f}s toks={len(out[0])}", flush=True)
    results.append({
        'id': item['id'],
        'seconds': sec,
        'tokens': int(len(out[0])),
        'abc_out': item['abc_out'],
    })

Path(spec['result_json']).write_text(json.dumps({
    'status': 'live_ok',
    'model_id': model_id,
    'params': int(params),
    'load_sec': round(load_sec, 2),
    'results': results,
}, indent=2), encoding='utf-8')
"""


def run_legato_batch(
    jobs: list[dict[str, Any]],
    work_dir: Path,
    max_new_tokens: int = 700,
    num_beams: int = 1,
    threads: int = 8,
) -> dict[str, Any]:
    """Runs live offline LEGATO bfloat16 inference over a batch of PNGs and converts ABC -> MusicXML."""
    work_dir.mkdir(parents=True, exist_ok=True)
    spec_path = work_dir / 'legato_spec.json'
    res_path = work_dir / 'legato_result.json'
    worker_py = work_dir / '_legato_worker.py'
    worker_py.write_text(_LEGATO_WORKER_CODE, encoding='utf-8')
    spec = {
        'model_id': 'guangyangmusic/legato',
        'max_new_tokens': max_new_tokens,
        'num_beams': num_beams,
        'threads': threads,
        'jobs': jobs,
        'result_json': str(res_path),
    }
    spec_path.write_text(json.dumps(spec, indent=2), encoding='utf-8')
    env = _offline_env({'LEGATO_REPO': str(LEGATO_REPO)}, threads=threads)
    proc = subprocess.run([str(TRANSFORMERS_PY), str(worker_py), str(spec_path)], env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f'LEGATO worker failed: {proc.stderr[-1200:]}')
    data = json.loads(res_path.read_text(encoding='utf-8'))
    if data.get('status') == 'live_ok':
        for item, res in zip(jobs, data['results']):
            abc_text = Path(res['abc_out']).read_text(encoding='utf-8')
            ok, conv_msg = abc_to_musicxml(abc_text, Path(item['xml_out']))
            res['xml_ok'] = ok
            res['xml_converter'] = conv_msg
            res['xml_out'] = item['xml_out']
    return data


def check_legato_offline(work_dir: Path) -> dict[str, Any]:
    """Verifies LEGATO LegatoModel import, offline load readiness, and ABC->MusicXML conversion."""
    work_dir.mkdir(parents=True, exist_ok=True)
    env = _offline_env({'PYTHONPATH': str(LEGATO_REPO)}, threads=4)
    probe = subprocess.run(
        [str(TRANSFORMERS_PY), '-c', (
            "import torch\n"
            "from legato.models import LegatoModel\n"
            "from transformers import AutoProcessor\n"
            "print('IMPORT_OK')\n"
            "try:\n"
            "    m = LegatoModel.from_pretrained('guangyangmusic/legato', local_files_only=True, torch_dtype=torch.bfloat16)\n"
            "    p = AutoProcessor.from_pretrained('guangyangmusic/legato', local_files_only=True)\n"
            "    print('LIVE_READY', sum(x.numel() for x in m.parameters()))\n"
            "except Exception as e:\n"
            "    print('GATED_SKIP', type(e).__name__, str(e)[:120])\n"
        )],
        env=env, capture_output=True, text=True,
    )
    out_txt = probe.stdout or ''
    import_ok = 'IMPORT_OK' in out_txt
    live_ready = 'LIVE_READY' in out_txt
    params = 0
    for ln in out_txt.splitlines():
        if ln.startswith('LIVE_READY'):
            params = int(ln.split()[1])

    sample_abc = (
        'X:1\nT:LEGATO Offline ABC Test\nM:4/4\nL:1/4\nK:G\n'
        'V:1 clef=treble\nG A B c | d2 B2 | c/2B/2 A G F | G4 |]\n'
        'V:2 clef=bass\nG,2 D,2 | G,2 G,2 | C, D, G, D, | G,4 |]\n'
    )
    xml_p = work_dir / 'legato_sample.musicxml'
    xml_ok, conv_msg = abc_to_musicxml(sample_abc, xml_p)
    xml_notes = sum(len(s) for s in read_musicxml(xml_p)['notes']) if xml_ok else 0

    import verovio  # noqa: PLC0415
    verovio.enableLog(verovio.LOG_OFF)
    tk = verovio.toolkit()
    verovio_abc_ok = bool(tk.loadData(sample_abc)) and tk.getPageCount() >= 1

    return {
        'import_ok': import_ok,
        'live_ready': live_ready,
        'params': params,
        'status': 'live_ready' if live_ready else 'gated_skipped (accept Llama-3.2-Vision license at https://huggingface.co/guangyangmusic/legato)',
        'abc2xml_ok': xml_ok and xml_notes >= 16,
        'abc2xml_notes': xml_notes,
        'abc2xml_msg': conv_msg,
        'verovio_abc_ok': verovio_abc_ok,
    }


def check_verovio_offline(work_dir: Path) -> dict[str, Any]:
    """Verifies Verovio offline SVG rendering across all 5 SMuFL fonts plus **kern and ABC conversion."""
    import verovio  # noqa: PLC0415
    verovio.enableLog(verovio.LOG_OFF)
    fonts = ('Leipzig', 'Bravura', 'Petaluma', 'Leland', 'Gootville')
    kern = '**kern\t**kern\n*clefF4\t*clefG2\n*k[f#]\t*k[f#]\n*M4/4\t*M4/4\n4G\t4g\n4A\t4a\n4B\t4b\n4c\t4cc\n=\t=\n2d\t2dd\n2r\t2r\n==\t==\n*-\t*-'
    abc = 'X:1\nM:3/4\nL:1/4\nK:C\nC D E | F G A | G3 |]\n'
    font_ok = {}
    for f in fonts:
        tk = verovio.toolkit()
        tk.setOptions({'font': f, 'scale': 40, 'svgViewBox': True})
        ok = bool(tk.loadData(kern))
        svg = tk.renderToSVG(1) if ok and tk.getPageCount() >= 1 else ''
        font_ok[f] = ('<svg' in svg and 'class="note"' in svg)
    tk_abc = verovio.toolkit()
    abc_ok = bool(tk_abc.loadData(abc)) and tk_abc.getPageCount() >= 1
    xml_out = work_dir / 'verovio_kern_test.musicxml'
    kern_xml_ok, conv_kind = kern_to_musicxml(kern, xml_out, title='verovio_kern')
    return {
        'version': verovio.toolkit().getVersion(),
        'fonts_ok': font_ok,
        'kern_svg_ok': all(font_ok.values()),
        'abc_svg_ok': abc_ok,
        'kern_to_musicxml_ok': kern_xml_ok,
        'kern_converter': conv_kind,
    }


# ---------------------------------------------------------------------------
# Head-to-head benchmark + complementary error analysis
# ---------------------------------------------------------------------------

def _complementary_analysis(
    case_id: str,
    gt_tokens: list[list[tuple]],
    tool_xmls: dict[str, list[Path]],
) -> dict[str, Any]:
    """Measures how many ScoreReader missed/wrong notes are recovered by external tools."""
    def _load_tokens(paths: list[Path]) -> list[list[tuple]]:
        staves: list[list[dict]] = []
        offset = Fraction(0)
        for p in paths:
            if not p.exists():
                continue
            try:
                parsed = read_musicxml(p)
            except Exception:
                continue
            for idx, notes in enumerate(parsed['notes']):
                while len(staves) <= idx:
                    staves.append([])
                staves[idx].extend(dict(n, on=n['on'] + offset) for n in notes)
            offset += parsed['length']
        joined = [join_ties(s) for s in staves]
        split = split_by_clef(joined, len(gt_tokens))
        return [reader_tokens(s) for s in split]

    sr_toks = _load_tokens(tool_xmls.get('scorereader', []))
    sr_chosen = match_staves(gt_tokens, sr_toks)
    sr_errors: dict[int, set[int]] = {}
    sr_err_total = 0
    for row, exp_tok in enumerate(gt_tokens):
        idx = sr_chosen[row]
        rd = sr_toks[idx] if idx is not None else []
        _, pairs = align_notes(exp_tok, rd)
        bad: set[int] = set()
        for r, k in pairs:
            if r is not None:
                if k is None or exp_tok[r][2] != rd[k][2] or exp_tok[r][1] != rd[k][1]:
                    bad.add(r)
                    sr_err_total += 1
        sr_errors[row] = bad

    recovered: dict[str, int] = {}
    for tool_name, paths in tool_xmls.items():
        if tool_name == 'scorereader':
            continue
        t_toks = _load_tokens(paths)
        t_chosen = match_staves(gt_tokens, t_toks)
        rec_cnt = 0
        for row, exp_tok in enumerate(gt_tokens):
            idx = t_chosen[row]
            rd = t_toks[idx] if idx is not None else []
            _, pairs = align_notes(exp_tok, rd)
            for r, k in pairs:
                if r is not None and k is not None and r in sr_errors[row]:
                    if exp_tok[r][2] == rd[k][2] and exp_tok[r][1] == rd[k][1]:
                        rec_cnt += 1
        recovered[tool_name] = rec_cnt
    return {'case': case_id, 'sr_errors': sr_err_total, 'recovered_by': recovered}


def prepare_benchmark_pages(
    out_dir: Path,
    dev_ids: tuple[str, ...] = STRATIFIED_DEV_IDS,
    verovio_ids: tuple[str, ...] = VEROVIO_SATB_IDS,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], Path]:
    """Prepares Clean Dev RGB PNGs (strictly clean_dev.json) and Verovio SATB ground-truth PNGs."""
    out_dir.mkdir(parents=True, exist_ok=True)
    png_dir = out_dir / 'pages_png'

    manifest = json.loads(CLEAN_DEV_MANIFEST.read_text(encoding='utf-8'))
    if manifest.get('split') != 'clean_dev':
        raise RuntimeError('Refused non-clean_dev manifest')
    truth_dir = Path(manifest['truth_dir'])
    dev_cases = [c for c in manifest['cases'] if c['id'] in set(dev_ids)]
    dev_cases.sort(key=lambda c: list(dev_ids).index(c['id']))

    page_records: list[dict[str, Any]] = []
    for case in dev_cases:
        cid = case['id']
        for page_num in case['pages']:
            stem = f'{cid}-p{page_num}'
            p_png = png_dir / f'{stem}.png'
            if not p_png.exists():
                render_pdf_page_rgb(Path(case['pdf']), page_num, p_png)
            page_records.append({'kind': 'clean_dev', 'case_id': cid, 'stem': stem, 'png': p_png, 'case': case})

    suite_map = {c['id']: c for c in build_roundtrip_suite()}
    verovio_cases: list[dict[str, Any]] = []
    for v_idx, vid in enumerate(verovio_ids):
        vcase = suite_map[vid]
        font = 'Bravura' if v_idx == 0 else 'Leipzig'
        gt_xml = out_dir / f'{vid}.gt.musicxml'
        if not gt_xml.exists():
            gt_xml.write_text(vcase['musicxml'], encoding='utf-8')
        v_png = png_dir / f'{vid}.png'
        if not v_png.exists():
            render_musicxml_to_png(vcase['musicxml'], font, v_png)
            ensure_rgb_png(v_png, v_png)
        vrec = {'id': vid, 'font': font, 'gt_xml': gt_xml, 'voices_per_staff': vcase['voices_per_staff']}
        verovio_cases.append(vrec)
        page_records.append({'kind': 'verovio_satb', 'case_id': vid, 'stem': vid, 'png': v_png, 'case': vrec})

    return dev_cases, verovio_cases, page_records, truth_dir


def run_benchmark(
    out_dir: Path,
    dev_ids: tuple[str, ...] = STRATIFIED_DEV_IDS,
    verovio_ids: tuple[str, ...] = VEROVIO_SATB_IDS,
    tools: tuple[str, ...] = ALL_TOOLS,
    eval_only: bool = False,
    oemer_workers: int = 2,
    legato_workers: int = 2,
    threads: int = 6,
) -> dict[str, Any]:
    """Runs selected tools offline into out_dir/<tool>/ and evaluates all present tools via eval_f1.py."""
    dev_cases, verovio_cases, page_records, truth_dir = prepare_benchmark_pages(out_dir, dev_ids, verovio_ids)
    sys_dir = out_dir / 'system_crops'

    if not eval_only:
        if 'scorereader' in tools:
            tdir = out_dir / 'scorereader'
            tdir.mkdir(parents=True, exist_ok=True)
            tmap: dict[str, float] = {}
            print('[scorereader] Running ScoreReader...', flush=True)
            for rec in page_records:
                out_xml = tdir / f"{rec['stem']}.musicxml"
                xml_text, sec = run_scorereader_on_png(rec['png'], title=rec['stem'])
                if xml_text:
                    out_xml.write_text(xml_text, encoding='utf-8')
                tmap[rec['stem']] = round(sec, 2)
                print(f"  scorereader {rec['stem']:34s}: {sec:5.2f}s", flush=True)
            (tdir / 'run_meta.json').write_text(json.dumps({'timings': tmap}, indent=2), encoding='utf-8')

        if 'oemer' in tools:
            tdir = out_dir / 'oemer'
            tdir.mkdir(parents=True, exist_ok=True)
            tmap = {}
            print(f'[oemer] Running oemer ONNX offline (workers={oemer_workers}, threads={threads})...', flush=True)

            def _do_oemer(rec: dict[str, Any]) -> tuple[str, dict[str, Any]]:
                res = run_oemer_on_png(rec['png'], tdir / f"{rec['stem']}.musicxml", threads=threads)
                print(f"  oemer       {rec['stem']:34s}: {res['seconds']:5.2f}s ok={res['ok']} {res['err'][:220]}", flush=True)
                return rec['stem'], res

            if oemer_workers > 1:
                with ThreadPoolExecutor(max_workers=oemer_workers) as pool:
                    for stem, res in pool.map(_do_oemer, page_records):
                        tmap[stem] = res['seconds']
            else:
                for rec in page_records:
                    stem, res = _do_oemer(rec)
                    tmap[stem] = res['seconds']
            (tdir / 'run_meta.json').write_text(json.dumps({'timings': tmap}, indent=2), encoding='utf-8')

        if 'smt_fp' in tools:
            tdir = out_dir / 'smt_fp'
            tdir.mkdir(parents=True, exist_ok=True)
            print(f'[smt_fp] Running SMT++ full-page (PRAIG/smt-fp-grandstaff, threads={threads})...', flush=True)
            fp_jobs = [
                {
                    'id': rec['stem'],
                    'images': [str(rec['png'])],
                    'kern_out': str(tdir / f"{rec['stem']}.krn"),
                    'xml_out': str(tdir / f"{rec['stem']}.musicxml"),
                }
                for rec in page_records
            ]
            fp_res = run_smt_batch('PRAIG/smt-fp-grandstaff', 'fp', fp_jobs, tdir, max_tokens=700, threads=threads)
            tmap = {r['id']: r['seconds'] for r in fp_res['results']}
            for r in fp_res['results']:
                print(f"  smt_fp      {r['id']:34s}: {r['seconds']:5.2f}s toks={r['tokens']} xml={r['xml_ok']}({r['xml_converter']})", flush=True)
            (tdir / 'run_meta.json').write_text(json.dumps({
                'timings': tmap, 'load_sec': fp_res['load_sec'], 'missing_keys': fp_res['missing_keys'],
            }, indent=2), encoding='utf-8')

        if 'smt_sys' in tools:
            tdir = out_dir / 'smt_sys'
            tdir.mkdir(parents=True, exist_ok=True)
            print(f'[smt_sys] Cropping systems with systems.py & running antoniorv6/smt-grandstaff (threads={threads})...', flush=True)
            sys_jobs = []
            for rec in page_records:
                crops = crop_systems_with_scorereader(rec['png'], sys_dir, rec['stem'])
                sys_jobs.append({
                    'id': rec['stem'],
                    'images': [c['path'] for c in crops],
                    'kern_out': str(tdir / f"{rec['stem']}.krn"),
                    'xml_out': str(tdir / f"{rec['stem']}.musicxml"),
                })
            sys_res = run_smt_batch('antoniorv6/smt-grandstaff', 'sys', sys_jobs, tdir, max_tokens=220, threads=threads)
            tmap = {r['id']: r['seconds'] for r in sys_res['results']}
            for r in sys_res['results']:
                print(f"  smt_sys     {r['id']:34s}: {r['seconds']:5.2f}s sys={r['systems']} toks={r['tokens']} xml={r['xml_ok']}({r['xml_converter']})", flush=True)
            (tdir / 'run_meta.json').write_text(json.dumps({
                'timings': tmap, 'load_sec': sys_res['load_sec'], 'missing_keys': sys_res['missing_keys'], 'is_legacy': sys_res['is_legacy'],
            }, indent=2), encoding='utf-8')

        if 'legato' in tools:
            tdir = out_dir / 'legato'
            tdir.mkdir(parents=True, exist_ok=True)
            print(f'[legato] Running LIVE offline LEGATO bfloat16 (workers={legato_workers}, threads={threads})...', flush=True)
            leg_jobs = [
                {
                    'id': rec['stem'],
                    'image': str(rec['png']),
                    'abc_out': str(tdir / f"{rec['stem']}.abc"),
                    'xml_out': str(tdir / f"{rec['stem']}.musicxml"),
                }
                for rec in page_records
            ]
            if legato_workers > 1 and len(leg_jobs) > 1:
                chunks = [leg_jobs[i::legato_workers] for i in range(legato_workers)]
                all_res: list[dict[str, Any]] = []
                status = 'live_ok'
                load_sec = 0.0
                params = 0
                with ThreadPoolExecutor(max_workers=legato_workers) as pool:
                    futs = [
                        pool.submit(run_legato_batch, ch, tdir / f'shard_{si}', 1600, 1, threads)
                        for si, ch in enumerate(chunks) if ch
                    ]
                    for fut in futs:
                        r = fut.result()
                        if r.get('status') != 'live_ok':
                            status = r.get('status', 'error')
                        load_sec = max(load_sec, float(r.get('load_sec') or 0.0))
                        params = max(params, int(r.get('params') or 0))
                        all_res.extend(r.get('results', []))
                leg_res = {'status': status, 'load_sec': load_sec, 'params': params, 'results': all_res}
            else:
                leg_res = run_legato_batch(leg_jobs, tdir, max_new_tokens=1600, num_beams=1, threads=threads)
            tmap = {r['id']: r['seconds'] for r in leg_res.get('results', [])}
            for r in leg_res.get('results', []):
                print(f"  legato      {r['id']:34s}: {r['seconds']:6.2f}s toks={r['tokens']} xml={r.get('xml_ok')}({r.get('xml_converter')})", flush=True)
            (tdir / 'run_meta.json').write_text(json.dumps({
                'timings': tmap, 'status': leg_res.get('status'), 'load_sec': leg_res.get('load_sec'), 'params': leg_res.get('params'),
            }, indent=2), encoding='utf-8')

    # Discover every evaluated tool present in out_dir
    eval_tools = [t for t in ALL_TOOLS if (out_dir / t / 'run_meta.json').exists()]
    if not eval_tools:
        eval_tools = list(tools)

    timings: dict[str, dict[str, float]] = {}
    tool_run_meta: dict[str, Any] = {}
    for t in eval_tools:
        mp = out_dir / t / 'run_meta.json'
        if mp.exists():
            meta = json.loads(mp.read_text(encoding='utf-8'))
            timings[t] = meta.get('timings', {})
            tool_run_meta[t] = meta
        else:
            timings[t] = {}

    legato_info = check_legato_offline(out_dir / 'legato_check')
    verovio_info = check_verovio_offline(out_dir / 'verovio_check')

    eval_summary: dict[str, Any] = {}
    per_case_scores: dict[str, dict[str, Any]] = {t: {} for t in eval_tools}

    for tool in eval_tools:
        tdir = out_dir / tool
        dev_p, dev_s, dev_r = Counter(), Counter(), Counter()
        dev_m_ok = dev_m_tot = 0
        for case in dev_cases:
            truth = json.loads((truth_dir / f"{case['id']}.json").read_text(encoding='utf-8'))
            sc = score_case(tdir, case, truth)
            per_case_scores[tool][case['id']] = {
                'parts_f1': prf(sc['parts']['right'], sc['parts']['expected'], sc['parts']['read'])[2],
                'staff_f1': prf(sc['staff']['right'], sc['staff']['expected'], sc['staff']['read'])[2],
                'rest_f1': prf(sc['rests']['matched'], sc['rests']['expected'], sc['rests']['actual'])[2],
                'meter_ok': sc['meter_ok'],
                'meter_actual': sc['meter_actual'],
                'meter_expected': sc['meter_expected'],
                'staff': sc['staff'],
                'parts': sc['parts'],
                'rests': sc['rests'],
            }
            dev_p.update(sc['parts'])
            dev_s.update(sc['staff'])
            dev_r.update(sc['rests'])
            if sc['meter_ok'] is not None:
                dev_m_tot += 1
                dev_m_ok += int(sc['meter_ok'])

        ver_p, ver_s, ver_r = Counter(), Counter(), Counter()
        ver_m_ok = ver_m_tot = 0
        for vc in verovio_cases:
            vid = vc['id']
            sc = score_musicxml_pair(vc['gt_xml'], tdir / f'{vid}.musicxml', vc['voices_per_staff'])
            per_case_scores[tool][vid] = {
                'parts_f1': sc['parts_f1'],
                'staff_f1': sc['staff_f1'],
                'rest_f1': sc['rests']['f1'],
                'meter_ok': sc['meter_ok'],
                'meter_actual': sc['meter_actual'],
                'meter_expected': sc['meter_expected'],
                'staff': sc['staff'],
                'parts': sc['parts'],
                'rests': sc['rests'],
            }
            ver_p.update(sc['parts'])
            ver_s.update(sc['staff'])
            ver_r.update({k: v for k, v in sc['rests'].items() if isinstance(v, int)})
            if sc['meter_ok'] is not None:
                ver_m_tot += 1
                ver_m_ok += int(sc['meter_ok'])

        all_sec = list(timings[tool].values())
        eval_summary[tool] = {
            'dev_parts_f1': prf(dev_p['right'], dev_p['expected'], dev_p['read'])[2],
            'dev_staff_f1': prf(dev_s['right'], dev_s['expected'], dev_s['read'])[2],
            'dev_staff_prec': prf(dev_s['right'], dev_s['expected'], dev_s['read'])[0],
            'dev_staff_rec': prf(dev_s['right'], dev_s['expected'], dev_s['read'])[1],
            'dev_rest_f1': prf(dev_r['matched'], dev_r['expected'], dev_r['actual'])[2],
            'dev_meter': f'{dev_m_ok}/{dev_m_tot}',
            'verovio_parts_f1': prf(ver_p['right'], ver_p['expected'], ver_p['read'])[2],
            'verovio_staff_f1': prf(ver_s['right'], ver_s['expected'], ver_s['read'])[2],
            'verovio_rest_f1': prf(ver_r['matched'], ver_r['expected'], ver_r['actual'])[2],
            'verovio_meter': f'{ver_m_ok}/{ver_m_tot}',
            'sec_per_page': round(float(np.mean(all_sec)), 2) if all_sec else 0.0,
            'total_pages': len(all_sec),
            **TOOL_META.get(tool, {}),
        }

    comp = []
    if 'scorereader' in eval_tools:
        for case in dev_cases:
            truth = json.loads((truth_dir / f"{case['id']}.json").read_text(encoding='utf-8'))
            gt_toks = [truth_tokens(truth, parts) for parts in case['layout']]
            t_paths = {t: [out_dir / t / f"{case['id']}-p{p}.musicxml" for p in case['pages']] for t in eval_tools}
            comp.append(_complementary_analysis(case['id'], gt_toks, t_paths))
        for vc in verovio_cases:
            gt = read_musicxml(vc['gt_xml'])
            gt_toks = [reader_tokens(join_ties(s)) for s in gt['notes']]
            t_paths = {t: [out_dir / t / f"{vc['id']}.musicxml"] for t in eval_tools}
            comp.append(_complementary_analysis(vc['id'], gt_toks, t_paths))

    report = {
        'summary': eval_summary,
        'per_case': per_case_scores,
        'complementary': comp,
        'run_meta': tool_run_meta,
        'legato': legato_info,
        'verovio': verovio_info,
        'timings': timings,
    }
    (out_dir / 'external_omr_benchmark.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


def print_summary(report: dict[str, Any]) -> None:
    print('\n=== HEAD-TO-HEAD EXTERNAL OMR BENCHMARK (Clean Dev 5 scores / 8 pages + 2 Verovio SATB) ===')
    print(f"{'Tool':12s} | {'Dev Staff F1':12s} | {'Dev Parts F1':12s} | {'Dev Rest F1':11s} | {'Dev Mtr':7s} | {'Ver Staff F1':12s} | {'Ver Rest':8s} | {'sec/pg':6s} | {'Size MB':7s}")
    print('-' * 114)
    for tool, s in report['summary'].items():
        print(
            f"{tool:12s} | {s['dev_staff_f1']:11.2%} | {s['dev_parts_f1']:11.2%} | "
            f"{s['dev_rest_f1']:10.2%} | {s['dev_meter']:7s} | {s['verovio_staff_f1']:11.2%} | "
            f"{s['verovio_rest_f1']:7.2%} | {s['sec_per_page']:6.2f} | {s['model_mb']:7.1f}"
        )
    print('\n--- Per-Case Staff F1 ---')
    tools = list(report['per_case'].keys())
    all_cases = list(report['per_case'][tools[0]].keys()) if tools else []
    header = f"{'Case':32s} | " + ' | '.join(f'{t:11s}' for t in tools)
    print(header)
    print('-' * len(header))
    for cid in all_cases:
        vals = ' | '.join(f"{report['per_case'][t][cid]['staff_f1']:10.2%}" for t in tools)
        print(f'{cid:32s} | {vals}')
    if report['complementary']:
        print('\n--- Complementary Errors (ScoreReader errors recovered by other tools) ---')
        for row in report['complementary']:
            print(f"  {row['case']:32s}: SR_err={row['sr_errors']:3d} | recovered={row['recovered_by']}")
    print('\n--- LEGATO Offline Check ---')
    print(' ', report['legato'])
    print('--- Verovio Offline Check ---')
    print(' ', report['verovio'])


def main() -> int:
    parser = argparse.ArgumentParser(description='Run offline head-to-head external OMR benchmark.')
    parser.add_argument('--out', default='/tmp/scorereader_swarm/omr_eval/external_bench', help='Output directory')
    parser.add_argument('--tools', default=','.join(ALL_TOOLS), help='Comma-separated tools to run')
    parser.add_argument('--eval-only', action='store_true', help='Skip inference and evaluate already-generated outputs')
    parser.add_argument('--oemer-workers', type=int, default=2, help='Parallel oemer page workers')
    parser.add_argument('--legato-workers', type=int, default=2, help='Parallel LEGATO worker shards')
    parser.add_argument('--threads', type=int, default=6, help='CPU threads per tool process')
    args = parser.parse_args()

    tools = tuple(t.strip() for t in args.tools.split(',') if t.strip())
    report = run_benchmark(
        Path(args.out),
        tools=tools,
        eval_only=args.eval_only,
        oemer_workers=args.oemer_workers,
        legato_workers=args.legato_workers,
        threads=args.threads,
    )
    print_summary(report)
    return 0


if __name__ == '__main__':
    sys.exit(main())

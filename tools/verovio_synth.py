#!/usr/bin/env python3
"""Multi-font engraved music crop generator powered by Verovio SVG DOM.

Renders diverse programmatic MusicXML scores with Verovio across five real SMuFL
fonts (Leipzig, Bravura, Petaluma, Leland, Gootville), rasterizes each page with
rsvg-convert, applies realistic scan degradations, and runs scorereader.layers.read_layers()
to extract exact, pixel-aligned training patches:

  1. verovio_synth_crops.npz : (N, 3, 32, 32) uint8 patches for all 19 SymNet classes
  2. verovio_stem_crops.npz  : (N, 3, 32, 32) uint8 canonical stem-tip patches (0/1/2 tails)
  3. verovio_time_crops.npz  : (N, 1, 24, 24) uint8 staff-row-bridged meter glyph patches

Zero holdout data is used. All data comes from programmatic MusicXML rendered offline.

Usage:
  PYTHONDONTWRITEBYTECODE=1 out/tools/omr-bench/verovio-venv/bin/python tools/verovio_synth.py \
      --out-dir /tmp/scorereader_swarm --workers 8
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import verovio

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scorereader.classify import CLASS_TO_ID, CLASSES, PATCH_SIZE, extract_patch, page_levels
from scorereader.layers import read_layers
from scorereader.meter import _free

SMUFL_FONTS = ('Leipzig', 'Bravura', 'Petaluma', 'Leland', 'Gootville')
STEM_CLASSES = ('tail_0', 'tail_1', 'tail_2')
TIME_CLASSES = ('2', '3', '4', '6', '8', '9', '12', 'C', 'cut', 'other')
TIME_TO_ID = {name: idx for idx, name in enumerate(TIME_CLASSES)}

STEM_SIZE = 32
STEM_SPACES = 4.5
TIME_SIZE = 24
RSVG_CONVERT = '/usr/bin/rsvg-convert'

# SMuFL codepoint prefixes used in Verovio SVG <use xlink:href="#E0A4-...">.
NOTEHEAD_SMUFL = {
    '#E0A4': 'head_filled',
    '#E0A3': 'head_hollow',
    '#E0A2': 'head_whole',
    '#E0A0': 'head_breve',
    '#E0A1': 'head_breve',
}
REST_SMUFL = {
    '#E4E3': 'rest_whole',
    '#E4E4': 'rest_half',
    '#E4E5': 'rest_quarter',
    '#E4E6': 'rest_eighth',
    '#E4E7': 'rest_16th',
}
ACCID_SMUFL = {
    '#E262': 'acc_sharp',
    '#E260': 'acc_flat',
    '#E261': 'acc_natural',
}
CLEF_SMUFL = {
    '#E050': 'clef_G',
    '#E07A': 'clef_G',
    '#E062': 'clef_F',
    '#E07C': 'clef_F',
    '#E05C': 'clef_C',
    '#E07B': 'clef_C',
}

SVG_NS = '{http://www.w3.org/2000/svg}'
XLINK_HREF = '{http://www.w3.org/1999/xlink}href'

_STEPS = ('C', 'D', 'E', 'F', 'G', 'A', 'B')
_LYRICS = (
    'Lord', 'have', 'mer', 'cy', 'A', 'men', 'Al', 'le', 'lu', 'ia',
    'Ho', 'ly', 'God', 'sing', 'praise', 'to', 'Thee', 'our', 'King', 'now',
)
_DYNAMICS = ('p', 'pp', 'ppp', 'mp', 'mf', 'f', 'ff', 'fff', 'fp', 'sf', 'sfz')


# ---------------------------------------------------------------------------
# Programmatic MusicXML builders
# ---------------------------------------------------------------------------

def _mxml_pitch(step: str, octave: int, alter: int = 0) -> str:
    alt = f'<alter>{alter}</alter>' if alter != 0 else ''
    return f'<pitch><step>{step}</step>{alt}<octave>{octave}</octave></pitch>'


def _mxml_note(
    step: str,
    octave: int,
    dur_type: str,
    div_dur: int,
    *,
    alter: int = 0,
    accidental: str | None = None,
    dot: bool = False,
    stem: str | None = None,
    voice: int = 1,
    staff: int = 1,
    chord: bool = False,
    beam: str | None = None,
    beam2: str | None = None,
    tie: str | None = None,
    slur: str | None = None,
    fermata: str | None = None,
    lyric: str | None = None,
) -> str:
    parts = ['<note>']
    if chord:
        parts.append('<chord/>')
    parts.append(_mxml_pitch(step, octave, alter))
    parts.append(f'<duration>{div_dur}</duration>')
    if tie in ('start', 'stop'):
        parts.append(f'<tie type="{tie}"/>')
    parts.append(f'<voice>{voice}</voice>')
    parts.append(f'<type>{dur_type}</type>')
    if dot:
        parts.append('<dot/>')
    if accidental:
        parts.append(f'<accidental>{accidental}</accidental>')
    if stem:
        parts.append(f'<stem>{stem}</stem>')
    parts.append(f'<staff>{staff}</staff>')
    if beam:
        parts.append(f'<beam number="1">{beam}</beam>')
    if beam2:
        parts.append(f'<beam number="2">{beam2}</beam>')
    notations = []
    if tie in ('start', 'stop'):
        notations.append(f'<tied type="{tie}"/>')
    if slur in ('start', 'stop'):
        notations.append(f'<slur type="{slur}" number="1"/>')
    if fermata == 'upright':
        notations.append('<fermata type="upright"/>')
    elif fermata == 'inverted':
        notations.append('<fermata type="inverted"/>')
    if notations:
        parts.append('<notations>' + ''.join(notations) + '</notations>')
    if lyric:
        parts.append(f'<lyric number="1"><text>{lyric}</text></lyric>')
    parts.append('</note>')
    return ''.join(parts)


def _mxml_rest(
    dur_type: str | None,
    div_dur: int,
    *,
    voice: int = 1,
    staff: int = 1,
    dot: bool = False,
    measure: bool = False,
    display: tuple[str, int] | None = None,
    fermata: str | None = None,
) -> str:
    parts = ['<note>']
    if measure:
        parts.append('<rest measure="yes"/>')
    elif display is not None:
        parts.append(f'<rest><display-step>{display[0]}</display-step><display-octave>{display[1]}</display-octave></rest>')
    else:
        parts.append('<rest/>')
    parts.append(f'<duration>{div_dur}</duration>')
    parts.append(f'<voice>{voice}</voice>')
    if dur_type:
        parts.append(f'<type>{dur_type}</type>')
    if dot:
        parts.append('<dot/>')
    parts.append(f'<staff>{staff}</staff>')
    if fermata:
        parts.append(f'<notations><fermata type="{fermata}"/></notations>')
    parts.append('</note>')
    return ''.join(parts)


def _mxml_dynamic(mark: str, staff: int = 1, placement: str = 'below') -> str:
    return (
        f'<direction placement="{placement}"><direction-type>'
        f'<dynamics><{mark}/></dynamics></direction-type><staff>{staff}</staff></direction>'
    )


def _mxml_time(beats: int, btype: int, sym: str | None = None) -> str:
    s_attr = f' symbol="{sym}"' if sym else ''
    return f'<time{s_attr}><beats>{beats}</beats><beat-type>{btype}</beat-type></time>'


def _mxml_clef(sign: str, line: int, num: int = 1) -> str:
    return f'<clef number="{num}"><sign>{sign}</sign><line>{line}</line></clef>'


def _wrap_score(measures_by_part: list[list[str]]) -> str:
    plist = []
    pbody = []
    for idx, measures in enumerate(measures_by_part, 1):
        plist.append(f'<score-part id="P{idx}"><part-name></part-name></score-part>')
        body = ''.join(f'<measure number="{m_i}">{m}</measure>' for m_i, m in enumerate(measures, 1))
        pbody.append(f'<part id="P{idx}">{body}</part>')
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<score-partwise version="3.1">'
        f'<part-list>{"".join(plist)}</part-list>'
        f'{"".join(pbody)}'
        '</score-partwise>'
    )


def _rand_pitch(rng: np.random.Generator, clef: str, ledger_bias: bool = False) -> tuple[str, int]:
    if clef == 'G':
        pool = [('A', 3), ('B', 3), ('C', 4), ('D', 4), ('E', 4), ('F', 4), ('G', 4), ('A', 4), ('B', 4),
                ('C', 5), ('D', 5), ('E', 5), ('F', 5), ('G', 5), ('A', 5), ('B', 5), ('C', 6)]
        if ledger_bias:
            pool = [('A', 3), ('B', 3), ('C', 4), ('G', 5), ('A', 5), ('B', 5), ('C', 6)]
    elif clef == 'F':
        pool = [('C', 2), ('D', 2), ('E', 2), ('F', 2), ('G', 2), ('A', 2), ('B', 2), ('C', 3), ('D', 3),
                ('E', 3), ('F', 3), ('G', 3), ('A', 3), ('B', 3), ('C', 4), ('D', 4), ('E', 4)]
        if ledger_bias:
            pool = [('C', 2), ('D', 2), ('E', 2), ('B', 3), ('C', 4), ('D', 4), ('E', 4)]
    else:
        pool = [('E', 3), ('F', 3), ('G', 3), ('A', 3), ('B', 3), ('C', 4), ('D', 4), ('E', 4), ('F', 4), ('G', 4), ('A', 4)]
    idx = int(rng.integers(0, len(pool)))
    return pool[idx]


def _step_shift(step: str, octave: int, delta: int) -> tuple[str, int]:
    pos = octave * 7 + _STEPS.index(step) + delta
    return _STEPS[pos % 7], pos // 7


def _build_template_satb(rng: np.random.Generator) -> str:
    """Two-staff SATB hymn with chords, dotted rhythms, beams, flags, ties, lyrics, dynamics, and fermatas."""
    fifths = int(rng.choice([-4, -3, -2, -1, 0, 1, 2, 3, 4]))
    meter_choices = [(4, 4, None), (3, 4, None), (2, 4, None), (2, 2, 'cut'), (4, 4, 'common'), (3, 2, None)]
    mb, mt, msym = meter_choices[int(rng.integers(0, len(meter_choices)))]
    measures: list[str] = []
    n_measures = 16
    for mi in range(n_measures):
        m = []
        if mi == 0:
            m.append(
                f'<attributes><divisions>4</divisions><key><fifths>{fifths}</fifths></key>'
                f'{_mxml_time(mb, mt, msym)}<staves>2</staves>'
                f'{_mxml_clef("G", 2, 1)}{_mxml_clef("F", 4, 2)}</attributes>'
            )
        elif mi % 4 == 0:
            m.append('<print new-system="yes"/>')

        if mi % 3 == 0:
            m.append(_mxml_dynamic(str(rng.choice(_DYNAMICS)), staff=1, placement='below'))

        # Staff 1: voice 1 (up) + voice 2 (down), 4 beats in divisions=4 (16 units)
        for st_idx, clef in ((1, 'G'), (2, 'F')):
            v_hi = 1 if st_idx == 1 else 5
            v_lo = 2 if st_idx == 1 else 6
            pattern = int(rng.integers(0, 6))
            if pattern == 0:
                # 4 quarters with occasional 2nd/3rd chord, accidental, fermata, lyric
                for b in range(4):
                    s1, o1 = _rand_pitch(rng, clef)
                    acc = str(rng.choice(['sharp', 'flat', 'natural'])) if rng.random() < 0.28 else None
                    alt = {'sharp': 1, 'flat': -1, 'natural': 0}.get(acc, 0)
                    fer = 'upright' if (b == 3 and st_idx == 1 and rng.random() < 0.45) else None
                    lyr = str(rng.choice(_LYRICS)) if (st_idx == 1 and rng.random() < 0.65) else None
                    sl = 'start' if b == 0 else ('stop' if b == 1 else None)
                    m.append(_mxml_note(s1, o1, 'quarter', 4, alter=alt, accidental=acc, stem='up',
                                        voice=v_hi, staff=st_idx, fermata=fer, lyric=lyr, slur=sl))
                    if rng.random() < 0.35:
                        s2, o2 = _step_shift(s1, o1, int(rng.choice([-1, -2])))
                        m.append(_mxml_note(s2, o2, 'quarter', 4, stem='up', voice=v_hi, staff=st_idx, chord=True))
                m.append('<backup><duration>16</duration></backup>')
                for b in range(2):
                    s3, o3 = _step_shift(*_rand_pitch(rng, clef), -3)
                    fer = 'inverted' if (b == 1 and st_idx == 2 and rng.random() < 0.40) else None
                    m.append(_mxml_note(s3, o3, 'half', 8, stem='down', voice=v_lo, staff=st_idx, fermata=fer))
            elif pattern == 1:
                # Beamed eighths + dotted quarter + flagged eighth
                for k in range(2):
                    s1, o1 = _rand_pitch(rng, clef)
                    m.append(_mxml_note(s1, o1, 'eighth', 2, stem='up', voice=v_hi, staff=st_idx,
                                        beam='begin' if k == 0 else 'end'))
                s1, o1 = _rand_pitch(rng, clef)
                m.append(_mxml_note(s1, o1, 'quarter', 6, dot=True, stem='up', voice=v_hi, staff=st_idx))
                s2, o2 = _rand_pitch(rng, clef)
                m.append(_mxml_note(s2, o2, 'eighth', 2, stem='up', voice=v_hi, staff=st_idx))
                s3, o3 = _rand_pitch(rng, clef)
                m.append(_mxml_note(s3, o3, 'quarter', 4, stem='up', voice=v_hi, staff=st_idx))
                m.append('<backup><duration>16</duration></backup>')
                s4, o4 = _rand_pitch(rng, clef)
                m.append(_mxml_note(s4, o4, 'half', 12, dot=True, stem='down', voice=v_lo, staff=st_idx))
                m.append(_mxml_rest('quarter', 4, voice=v_lo, staff=st_idx))
            elif pattern == 2:
                # Beamed 16ths + flagged 16th + quarter rest + half note
                for k in range(4):
                    s1, o1 = _rand_pitch(rng, clef)
                    bm = 'begin' if k == 0 else ('end' if k == 3 else 'continue')
                    m.append(_mxml_note(s1, o1, '16th', 1, stem='up', voice=v_hi, staff=st_idx, beam=bm, beam2=bm))
                m.append(_mxml_rest('quarter', 4, voice=v_hi, staff=st_idx))
                s2, o2 = _rand_pitch(rng, clef)
                m.append(_mxml_note(s2, o2, 'half', 8, stem='up', voice=v_hi, staff=st_idx))
                m.append('<backup><duration>16</duration></backup>')
                for k in range(4):
                    s3, o3 = _rand_pitch(rng, clef)
                    m.append(_mxml_note(s3, o3, 'quarter', 4, stem='down', voice=v_lo, staff=st_idx))
            elif pattern == 3:
                # Whole note in voice 1 + half rest + half note in voice 2
                s1, o1 = _rand_pitch(rng, clef, ledger_bias=rng.random() < 0.4)
                acc = str(rng.choice(['sharp', 'flat', 'natural'])) if rng.random() < 0.35 else None
                alt = {'sharp': 1, 'flat': -1, 'natural': 0}.get(acc, 0)
                m.append(_mxml_note(s1, o1, 'whole', 16, alter=alt, accidental=acc, voice=v_hi, staff=st_idx))
                m.append('<backup><duration>16</duration></backup>')
                m.append(_mxml_rest('half', 8, voice=v_lo, staff=st_idx))
                s2, o2 = _rand_pitch(rng, clef)
                m.append(_mxml_note(s2, o2, 'half', 8, stem='down', voice=v_lo, staff=st_idx))
            elif pattern == 4:
                # Dotted eighth + 16th beamlet stub + flagged 8th + 8th rest + quarter + quarter
                s1, o1 = _rand_pitch(rng, clef)
                s2, o2 = _step_shift(s1, o1, 1)
                m.append(_mxml_note(s1, o1, 'eighth', 3, dot=True, stem='up', voice=v_hi, staff=st_idx, beam='begin'))
                m.append(_mxml_note(s2, o2, '16th', 1, stem='up', voice=v_hi, staff=st_idx, beam='end', beam2='backward hook'))
                s3, o3 = _rand_pitch(rng, clef)
                m.append(_mxml_note(s3, o3, 'eighth', 2, stem='up', voice=v_hi, staff=st_idx))
                m.append(_mxml_rest('eighth', 2, voice=v_hi, staff=st_idx))
                m.append(_mxml_rest('16th', 1, voice=v_hi, staff=st_idx))
                s4, o4 = _rand_pitch(rng, clef)
                m.append(_mxml_note(s4, o4, '16th', 1, stem='up', voice=v_hi, staff=st_idx))
                m.append(_mxml_rest('eighth', 2, voice=v_hi, staff=st_idx))
                s5, o5 = _rand_pitch(rng, clef)
                m.append(_mxml_note(s5, o5, 'quarter', 4, stem='up', voice=v_hi, staff=st_idx))
                m.append('<backup><duration>16</duration></backup>')
                for k in range(2):
                    s6, o6 = _rand_pitch(rng, clef)
                    m.append(_mxml_note(s6, o6, 'half', 8, stem='down', voice=v_lo, staff=st_idx))
            else:
                # Stacked 2-voice rests + notes with ties
                m.append(_mxml_rest('quarter', 4, voice=v_hi, staff=st_idx))
                s1, o1 = _rand_pitch(rng, clef)
                m.append(_mxml_note(s1, o1, 'quarter', 4, stem='up', voice=v_hi, staff=st_idx, tie='start'))
                m.append(_mxml_note(s1, o1, 'half', 8, stem='up', voice=v_hi, staff=st_idx, tie='stop'))
                m.append('<backup><duration>16</duration></backup>')
                m.append(_mxml_rest('quarter', 4, voice=v_lo, staff=st_idx))
                s2, o2 = _rand_pitch(rng, clef)
                m.append(_mxml_note(s2, o2, 'half', 12, dot=True, stem='down', voice=v_lo, staff=st_idx))
            if st_idx == 1:
                m.append('<backup><duration>16</duration></backup>')
        measures.append(''.join(m))
    return _wrap_score([measures])


def _build_template_rests_and_rare(rng: np.random.Generator) -> str:
    """High-density showcase of all 5 rest types (centered + ledger-shifted), breves, wholes, dots, fermatas, dynamics."""
    clefs = [('G', 2), ('F', 4), ('C', 3), ('C', 4)]
    c_sign, c_line = clefs[int(rng.integers(0, len(clefs)))]
    fifths = int(rng.choice([-5, -2, 0, 2, 5]))
    measures: list[str] = []
    for mi in range(18):
        m = []
        if mi == 0:
            m.append(
                f'<attributes><divisions>4</divisions><key><fifths>{fifths}</fifths></key>'
                f'{_mxml_time(4, 4)}<staves>2</staves>'
                f'{_mxml_clef(c_sign, c_line, 1)}{_mxml_clef("F", 4, 2)}</attributes>'
            )
        elif mi % 3 == 0:
            m.append('<print new-system="yes"/>')

        kind = mi % 6
        if kind == 0:
            # Whole rests (measure rest + explicit + ledger shifted) and half rests (normal + ledger)
            m.append(_mxml_rest(None, 16, voice=1, staff=1, measure=True))
            m.append('<backup><duration>16</duration></backup>')
            m.append(_mxml_rest('whole', 16, voice=5, staff=2, display=('E', 4)))
        elif kind == 1:
            # Ledger-line shifted half and whole rests in two voices
            m.append(_mxml_rest('half', 8, voice=1, staff=1, display=('A', 5), fermata='upright'))
            m.append(_mxml_rest('half', 8, voice=1, staff=1, display=('B', 4)))
            m.append('<backup><duration>16</duration></backup>')
            m.append(_mxml_rest('half', 8, voice=2, staff=1, display=('A', 3)))
            m.append(_mxml_rest('half', 8, voice=2, staff=1, display=('D', 4)))
            m.append('<backup><duration>16</duration></backup>')
            m.append(_mxml_rest('whole', 16, voice=5, staff=2, display=('D', 2)))
        elif kind == 2:
            # Quarter, eighth, and 16th rests (dotted and stacked)
            m.append(_mxml_dynamic(str(rng.choice(_DYNAMICS)), staff=1, placement='below'))
            m.append(_mxml_rest('quarter', 6, voice=1, staff=1, dot=True))
            m.append(_mxml_rest('eighth', 2, voice=1, staff=1))
            m.append(_mxml_rest('16th', 1, voice=1, staff=1))
            m.append(_mxml_rest('16th', 1, voice=1, staff=1))
            m.append(_mxml_rest('eighth', 2, voice=1, staff=1))
            m.append(_mxml_rest('quarter', 4, voice=1, staff=1))
            m.append('<backup><duration>16</duration></backup>')
            m.append(_mxml_rest('quarter', 4, voice=2, staff=1, display=('E', 4)))
            m.append(_mxml_rest('eighth', 3, voice=2, staff=1, dot=True, display=('E', 4)))
            m.append(_mxml_rest('16th', 1, voice=2, staff=1, display=('E', 4)))
            m.append(_mxml_rest('quarter', 4, voice=2, staff=1, display=('D', 4)))
            m.append(_mxml_rest('quarter', 4, voice=2, staff=1, display=('E', 4)))
            m.append('<backup><duration>16</duration></backup>')
            m.append(_mxml_rest('quarter', 4, voice=5, staff=2))
            m.append(_mxml_rest('eighth', 2, voice=5, staff=2))
            m.append(_mxml_rest('16th', 1, voice=5, staff=2))
            m.append(_mxml_rest('16th', 1, voice=5, staff=2))
            m.append(_mxml_rest('half', 8, voice=5, staff=2, fermata='inverted'))
        elif kind == 3:
            # Breve notes (in 4/2 measure) + whole notes on ledger lines
            m.append(f'<attributes>{_mxml_time(4, 2)}</attributes>')
            s1, o1 = _rand_pitch(rng, c_sign, ledger_bias=rng.random() < 0.4)
            m.append(_mxml_note(s1, o1, 'breve', 32, voice=1, staff=1, fermata='upright'))
            m.append('<backup><duration>32</duration></backup>')
            s2, o2 = _rand_pitch(rng, 'F', ledger_bias=rng.random() < 0.4)
            m.append(_mxml_note(s2, o2, 'breve', 32, voice=5, staff=2))
        elif kind == 4:
            # Whole notes (dotted + stacked chords) & hollow half notes
            m.append(f'<attributes>{_mxml_time(4, 4)}</attributes>')
            s1, o1 = _rand_pitch(rng, c_sign, ledger_bias=rng.random() < 0.4)
            m.append(_mxml_note(s1, o1, 'whole', 16, voice=1, staff=1))
            s1b, o1b = _step_shift(s1, o1, -2)
            m.append(_mxml_note(s1b, o1b, 'whole', 16, voice=1, staff=1, chord=True))
            m.append('<backup><duration>16</duration></backup>')
            s2, o2 = _rand_pitch(rng, 'F')
            m.append(_mxml_note(s2, o2, 'half', 12, dot=True, stem='down', voice=5, staff=2))
            m.append(_mxml_rest('quarter', 4, voice=5, staff=2))
        else:
            # Dense 16th rests, 8th rests, quarter rests, and dotted notes with dynamics
            m.append(_mxml_dynamic(str(rng.choice(_DYNAMICS)), staff=2, placement='above'))
            for _ in range(4):
                m.append(_mxml_rest('16th', 1, voice=1, staff=1))
                s1, o1 = _rand_pitch(rng, c_sign)
                m.append(_mxml_note(s1, o1, '16th', 1, stem=str(rng.choice(['up', 'down'])), voice=1, staff=1))
                m.append(_mxml_rest('eighth', 2, voice=1, staff=1))
            m.append('<backup><duration>16</duration></backup>')
            for _ in range(2):
                s2, o2 = _rand_pitch(rng, 'F')
                m.append(_mxml_note(s2, o2, 'quarter', 6, dot=True, stem='up', voice=5, staff=2))
                m.append(_mxml_rest('eighth', 2, voice=5, staff=2))
        measures.append(''.join(m))
    return _wrap_score([measures])


def _build_template_accidentals_clefs_meters(rng: np.random.Generator) -> str:
    """High-density showcase of all 10 TimeNet meter classes, G/F/C clefs, and sharp/flat/natural accidentals."""
    all_meters = [
        (2, 2, None), (2, 4, None), (3, 4, None), (4, 4, None), (3, 2, None),
        (6, 8, None), (9, 8, None), (12, 8, None), (6, 4, None), (9, 4, None),
        (12, 4, None), (4, 4, 'common'), (2, 2, 'cut'), (3, 8, None), (2, 8, None), (4, 2, None),
    ]
    rng.shuffle(all_meters)
    clef_cycle = [('G', 2), ('F', 4), ('C', 3), ('C', 4)]
    key_cycle = [-5, -4, -3, -2, -1, 1, 2, 3, 4, 5]
    measures: list[str] = []
    for mi, (mb, mt, msym) in enumerate(all_meters):
        m = []
        c1s, c1l = clef_cycle[mi % len(clef_cycle)]
        c2s, c2l = clef_cycle[(mi + 1) % len(clef_cycle)]
        kf = key_cycle[mi % len(key_cycle)]
        if mi == 0:
            m.append(
                f'<attributes><divisions>4</divisions><key><fifths>{kf}</fifths></key>'
                f'{_mxml_time(mb, mt, msym)}<staves>2</staves>'
                f'{_mxml_clef(c1s, c1l, 1)}{_mxml_clef(c2s, c2l, 2)}</attributes>'
            )
        else:
            if mi % 3 == 0:
                m.append('<print new-system="yes"/>')
            m.append(
                f'<attributes><key><fifths>{kf}</fifths></key>'
                f'{_mxml_time(mb, mt, msym)}'
                f'{_mxml_clef(c1s, c1l, 1)}{_mxml_clef(c2s, c2l, 2)}</attributes>'
            )
        # Fill 2 beats of notes carrying explicit sharp, flat, and natural accidentals
        accs = ['sharp', 'flat', 'natural']
        for st_idx, c_sign in ((1, c1s), (2, c2s)):
            v = 1 if st_idx == 1 else 5
            for b in range(3):
                acc = accs[(mi + b + st_idx) % 3]
                alt = {'sharp': 1, 'flat': -1, 'natural': 0}[acc]
                s1, o1 = _rand_pitch(rng, c_sign)
                dur_t = 'quarter' if b < 2 else 'half'
                dur_d = 4 if b < 2 else 8
                st_dir = 'up' if rng.random() < 0.5 else 'down'
                m.append(_mxml_note(s1, o1, dur_t, dur_d, alter=alt, accidental=acc, stem=st_dir, voice=v, staff=st_idx))
            if st_idx == 1:
                m.append('<backup><duration>16</duration></backup>')
        measures.append(''.join(m))
    return _wrap_score([measures])


def _build_template_stems_beams_flags(rng: np.random.Generator) -> str:
    """Dense StemNet showcase: 0-tail quarters (with slurs/lyrics/fermatas), 1-tail 8ths, 2-tail 16ths (beamed+flagged+stubs)."""
    fifths = int(rng.choice([-3, -1, 0, 1, 3]))
    measures: list[str] = []
    for mi in range(16):
        m = []
        if mi == 0:
            m.append(
                f'<attributes><divisions>4</divisions><key><fifths>{fifths}</fifths></key>'
                f'{_mxml_time(4, 4)}<staves>2</staves>'
                f'{_mxml_clef("G", 2, 1)}{_mxml_clef("F", 4, 2)}</attributes>'
            )
        elif mi % 4 == 0:
            m.append('<print new-system="yes"/>')

        for st_idx, clef in ((1, 'G'), (2, 'F')):
            v = 1 if st_idx == 1 else 5
            st_dir = 'up' if (mi + st_idx) % 2 == 0 else 'down'
            mode = mi % 5
            if mode == 0:
                # Plain quarters with slurs, lyrics, fermatas, and accidentals near tips (hard tail_0)
                for b in range(4):
                    s1, o1 = _rand_pitch(rng, clef, ledger_bias=rng.random() < 0.35)
                    lyr = str(rng.choice(_LYRICS))
                    sl = 'start' if b in (0, 2) else 'stop'
                    fer = ('upright' if st_dir == 'up' else 'inverted') if b == 3 else None
                    m.append(_mxml_note(s1, o1, 'quarter', 4, stem=st_dir, voice=v, staff=st_idx,
                                        slur=sl, lyric=lyr, fermata=fer))
            elif mode == 1:
                # Flagged eighths + beamed eighths (tail_1)
                for _ in range(2):
                    s1, o1 = _rand_pitch(rng, clef)
                    m.append(_mxml_note(s1, o1, 'eighth', 2, stem=st_dir, voice=v, staff=st_idx))
                    m.append(_mxml_rest('eighth', 2, voice=v, staff=st_idx))
                for k in range(4):
                    s1, o1 = _rand_pitch(rng, clef)
                    bm = 'begin' if k == 0 else ('end' if k == 3 else 'continue')
                    m.append(_mxml_note(s1, o1, 'eighth', 2, stem=st_dir, voice=v, staff=st_idx, beam=bm))
            elif mode == 2:
                # Flagged 16ths + beamed 16ths (tail_2)
                for _ in range(2):
                    s1, o1 = _rand_pitch(rng, clef)
                    m.append(_mxml_note(s1, o1, '16th', 1, stem=st_dir, voice=v, staff=st_idx))
                    m.append(_mxml_rest('16th', 1, voice=v, staff=st_idx))
                    s2, o2 = _rand_pitch(rng, clef)
                    m.append(_mxml_note(s2, o2, '16th', 1, stem=st_dir, voice=v, staff=st_idx))
                    m.append(_mxml_rest('16th', 1, voice=v, staff=st_idx))
                for _ in range(2):
                    for k in range(4):
                        s1, o1 = _rand_pitch(rng, clef)
                        bm = 'begin' if k == 0 else ('end' if k == 3 else 'continue')
                        m.append(_mxml_note(s1, o1, '16th', 1, stem=st_dir, voice=v, staff=st_idx, beam=bm, beam2=bm))
            elif mode == 3:
                # Dotted eighth + 16th pairs (tail_1 + tail_2 stub)
                for _ in range(4):
                    s1, o1 = _rand_pitch(rng, clef)
                    s2, o2 = _step_shift(s1, o1, int(rng.choice([-1, 1])))
                    m.append(_mxml_note(s1, o1, 'eighth', 3, dot=True, stem=st_dir, voice=v, staff=st_idx, beam='begin'))
                    m.append(_mxml_note(s2, o2, '16th', 1, stem=st_dir, voice=v, staff=st_idx, beam='end', beam2='backward hook'))
            else:
                # Mixed 8th + two 16ths + quarter
                for _ in range(2):
                    s1, o1 = _rand_pitch(rng, clef)
                    s2, o2 = _step_shift(s1, o1, 1)
                    s3, o3 = _step_shift(s1, o1, 2)
                    m.append(_mxml_note(s1, o1, 'eighth', 2, stem=st_dir, voice=v, staff=st_idx, beam='begin'))
                    m.append(_mxml_note(s2, o2, '16th', 1, stem=st_dir, voice=v, staff=st_idx, beam='continue', beam2='begin'))
                    m.append(_mxml_note(s3, o3, '16th', 1, stem=st_dir, voice=v, staff=st_idx, beam='end', beam2='end'))
                    s4, o4 = _rand_pitch(rng, clef)
                    m.append(_mxml_note(s4, o4, 'quarter', 4, stem=st_dir, voice=v, staff=st_idx,
                                        lyric=str(rng.choice(_LYRICS))))
            if st_idx == 1:
                m.append('<backup><duration>16</duration></backup>')
        measures.append(''.join(m))
    return _wrap_score([measures])


TEMPLATES = (
    ('satb', _build_template_satb),
    ('rests_rare', _build_template_rests_and_rare),
    ('acc_clef_meter', _build_template_accidentals_clefs_meters),
    ('stems_beams', _build_template_stems_beams_flags),
)


# ---------------------------------------------------------------------------
# SVG coordinate parsing and scan degradation
# ---------------------------------------------------------------------------

def _parse_transform(tf: str) -> tuple[float, float, float, float]:
    """Parses translate(tx, ty) and scale(sx, sy) from an SVG transform attribute."""
    tx, ty, sx, sy = 0.0, 0.0, 1.0, 1.0
    if not tf:
        return tx, ty, sx, sy
    m_t = re.search(r'translate\(\s*([-\d.]+)(?:[\s,]+([-\d.]+))?\s*\)', tf)
    if m_t:
        tx = float(m_t.group(1))
        ty = float(m_t.group(2) or 0.0)
    m_s = re.search(r'scale\(\s*([-\d.]+)(?:[\s,]+([-\d.]+))?\s*\)', tf)
    if m_s:
        sx = float(m_s.group(1))
        sy = float(m_s.group(2) or sx)
    return tx, ty, sx, sy


def _direct_bbox(el: ET.Element) -> tuple[float, float, float, float] | None:
    """Returns (x0, y0, x1, y1) from a direct child '<g class="... bounding-box"><rect .../></g>'."""
    for child in el:
        if 'bounding-box' in child.attrib.get('class', ''):
            rect = child.find(f'{SVG_NS}rect')
            if rect is not None:
                w = float(rect.attrib.get('width', 0.0))
                h = float(rect.attrib.get('height', 0.0))
                if w > 0.0 and h > 0.0:
                    x = float(rect.attrib.get('x', 0.0))
                    y = float(rect.attrib.get('y', 0.0))
                    return x, y, x + w, y + h
    return None


def _first_use_href(el: ET.Element) -> tuple[str | None, tuple[float, float] | None]:
    """Returns the first SMuFL '#EXXX' glyph code and its translate(x, y) inside el."""
    for u in el.iter():
        if u.tag == f'{SVG_NS}use':
            href = u.attrib.get(XLINK_HREF) or u.attrib.get('href') or ''
            code = href.split('-', 1)[0] if href.startswith('#') else None
            tx, ty, _, _ = _parse_transform(u.attrib.get('transform', ''))
            return code, (tx, ty)
    return None, None


def _render_svg_to_grey(svg_text: str, width_px: int) -> np.ndarray:
    """Rasterizes a Verovio SVG string to a uint8 grayscale PNG using rsvg-convert."""
    proc = subprocess.run(
        [RSVG_CONVERT, '-b', 'white', '-w', str(width_px)],
        input=svg_text.encode('utf-8'),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    arr = np.frombuffer(proc.stdout, dtype=np.uint8)
    grey = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    if grey is None:
        raise RuntimeError('rsvg-convert produced an unreadable PNG buffer')
    return grey


def _extract_svg_annotations(svg_text: str, png_w: int, png_h: int) -> dict[str, Any]:
    """Parses Verovio SVG DOM into exact PNG-pixel staves, symbols, stems, meters, and negatives."""
    root = ET.fromstring(svg_text)
    def_svg = next((c for c in root if c.tag == f'{SVG_NS}svg'), root)
    vb = [float(v) for v in def_svg.attrib.get('viewBox', '0 0 21000 29700').split()]
    scale_x = png_w / max(1.0, vb[2])
    scale_y = png_h / max(1.0, vb[3])

    def to_px(x: float, y: float, off_x: float, off_y: float) -> tuple[float, float]:
        return (x + off_x) * scale_x, (y + off_y) * scale_y

    def box_to_px(box: tuple[float, float, float, float], off_x: float, off_y: float) -> tuple[float, float, float, float]:
        x0, y0 = to_px(box[0], box[1], off_x, off_y)
        x1, y1 = to_px(box[2], box[3], off_x, off_y)
        return x0, y0, x1, y1

    systems_staves: list[list[dict]] = []
    symbols: list[dict] = []
    stems: list[dict] = []
    meters: list[dict] = []
    negatives: list[dict] = []

    def walk(
        el: ET.Element,
        off_x: float,
        off_y: float,
        cur_sys: int,
        cur_staff_rows: list[float] | None,
        cur_chord_dur: str | None,
    ) -> None:
        tx, ty, _, _ = _parse_transform(el.attrib.get('transform', ''))
        ox, oy = off_x + tx, off_y + ty
        cls = el.attrib.get('class', '')

        if cls == 'system':
            cur_sys = len(systems_staves)
            systems_staves.append([])

        if cls == 'staff':
            ys_lines: list[float] = []
            xs_min: list[float] = []
            xs_max: list[float] = []
            for child in el:
                if child.tag == f'{SVG_NS}path':
                    d = child.attrib.get('d', '')
                    m = re.match(r'^M\s*([-\d.]+)\s+([-\d.]+)\s+L\s*([-\d.]+)\s+([-\d.]+)$', d.strip())
                    if m:
                        x_a, y_a, x_b, y_b = float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))
                        if abs(y_a - y_b) <= 2.0 and abs(x_b - x_a) > 200.0:
                            px0, py0 = to_px(min(x_a, x_b), y_a, ox, oy)
                            px1, _ = to_px(max(x_a, x_b), y_b, ox, oy)
                            ys_lines.append(py0)
                            xs_min.append(px0)
                            xs_max.append(px1)
            if len(ys_lines) == 5 and cur_sys >= 0:
                ys_sorted = sorted(ys_lines)
                st_rec = {
                    'rows': ys_sorted,
                    'x0': min(xs_min),
                    'x1': max(xs_max),
                    'space': float(np.median(np.diff(ys_sorted))),
                }
                # Merge horizontally across measures of the same staff in one system.
                merged = False
                for existing in systems_staves[cur_sys]:
                    if abs(existing['rows'][2] - st_rec['rows'][2]) < 0.6 * st_rec['space']:
                        existing['x0'] = min(existing['x0'], st_rec['x0'])
                        existing['x1'] = max(existing['x1'], st_rec['x1'])
                        merged = True
                        break
                if not merged:
                    systems_staves[cur_sys].append(st_rec)
                cur_staff_rows = ys_sorted

        if cls == 'chord':
            cur_chord_dur = el.attrib.get('data-dur') or cur_chord_dur

        # Extract notehead symbol
        if cls == 'note':
            dur = el.attrib.get('data-dur') or cur_chord_dur
            nh_el = next((c for c in el if c.attrib.get('class') == 'notehead'), None)
            code, _ = _first_use_href(nh_el) if nh_el is not None else _first_use_href(el)
            cls_name = NOTEHEAD_SMUFL.get(code or '')
            if cls_name is None and dur:
                cls_name = {'breve': 'head_breve', '1': 'head_whole', '2': 'head_hollow',
                            '4': 'head_filled', '8': 'head_filled', '16': 'head_filled'}.get(dur)
            bb = _direct_bbox(el)
            if cls_name and bb:
                x0, y0, x1, y1 = box_to_px(bb, ox, oy)
                symbols.append({'cls': cls_name, 'cx': 0.5 * (x0 + x1), 'cy': 0.5 * (y0 + y1), 'box': (x0, y0, x1, y1)})

            # Extract single-note stem (chord stems are handled under 'chord')
            if dur in ('4', '8', '16') and cls_name == 'head_filled':
                st_el = next((c for c in el if c.attrib.get('class') == 'stem'), None)
                if st_el is not None:
                    sbb = _direct_bbox(st_el)
                    if sbb:
                        sx0, sy0, sx1, sy1 = box_to_px(sbb, ox, oy)
                        sdir = st_el.attrib.get('data-dir')
                        if sdir not in ('up', 'down') and bb:
                            _, ny0, _, ny1 = box_to_px(bb, ox, oy)
                            sdir = 'up' if sy0 < 0.5 * (ny0 + ny1) - 1.0 else 'down'
                        if sdir in ('up', 'down'):
                            tails = {'4': 0, '8': 1, '16': 2}[dur]
                            send = sy0 if sdir == 'up' else sy1
                            stems.append({'x': 0.5 * (sx0 + sx1), 'end': send, 'dir': sdir, 'tails': tails})
                            # Hard negative: down-stem neck below filled head (classic eighth-rest FP)
                            if sdir == 'down' and bb:
                                _, ny0, _, ny1 = box_to_px(bb, ox, oy)
                                negatives.append({'kind': 'down_stem_neck', 'cx': 0.5 * (sx0 + sx1),
                                                  'cy': 0.5 * (ny0 + ny1) + 0.55 * (sy1 - 0.5 * (ny0 + ny1))})

        # Extract chord-level stem
        if cls == 'chord' and cur_chord_dur in ('4', '8', '16'):
            st_el = next((c for c in el if c.attrib.get('class') == 'stem'), None)
            if st_el is not None:
                sbb = _direct_bbox(st_el)
                if sbb:
                    sx0, sy0, sx1, sy1 = box_to_px(sbb, ox, oy)
                    sdir = st_el.attrib.get('data-dir')
                    if sdir in ('up', 'down'):
                        tails = {'4': 0, '8': 1, '16': 2}[cur_chord_dur]
                        send = sy0 if sdir == 'up' else sy1
                        stems.append({'x': 0.5 * (sx0 + sx1), 'end': send, 'dir': sdir, 'tails': tails})

        if cls in ('rest', 'mRest'):
            code, _ = _first_use_href(el)
            rcls = REST_SMUFL.get(code or '')
            if rcls is None:
                dur = el.attrib.get('data-dur')
                rcls = 'rest_whole' if cls == 'mRest' else {'1': 'rest_whole', '2': 'rest_half',
                                                            '4': 'rest_quarter', '8': 'rest_eighth',
                                                            '16': 'rest_16th'}.get(dur or '')
            bb = _direct_bbox(el)
            if rcls and bb:
                x0, y0, x1, y1 = box_to_px(bb, ox, oy)
                symbols.append({'cls': rcls, 'cx': 0.5 * (x0 + x1), 'cy': 0.5 * (y0 + y1), 'box': (x0, y0, x1, y1)})

        if cls == 'accid':
            code, _ = _first_use_href(el)
            acls = ACCID_SMUFL.get(code or '')
            if acls is None:
                acls = {'s': 'acc_sharp', 'f': 'acc_flat', 'n': 'acc_natural'}.get(el.attrib.get('data-accid', ''))
            bb = _direct_bbox(el)
            if acls and bb:
                x0, y0, x1, y1 = box_to_px(bb, ox, oy)
                symbols.append({'cls': acls, 'cx': 0.5 * (x0 + x1), 'cy': 0.5 * (y0 + y1), 'box': (x0, y0, x1, y1)})

        if cls == 'keyAccid':
            code, pos = _first_use_href(el)
            acls = ACCID_SMUFL.get(code or '')
            if acls and pos is not None:
                sp_svg = 180.0
                dx_svg = 0.42 * sp_svg if acls != 'acc_natural' else 0.34 * sp_svg
                dy_svg = -0.32 * sp_svg if acls == 'acc_flat' else 0.0
                cx, cy = to_px(pos[0] + dx_svg, pos[1] + dy_svg, ox, oy)
                symbols.append({'cls': acls, 'cx': cx, 'cy': cy, 'box': None, 'refine': True})

        if cls == 'clef':
            code, _ = _first_use_href(el)
            ccls = CLEF_SMUFL.get(code or '')
            if ccls is None:
                ccls = {'G': 'clef_G', 'F': 'clef_F', 'C': 'clef_C'}.get(el.attrib.get('data-shape', ''))
            bb = _direct_bbox(el)
            if ccls and bb:
                x0, y0, x1, y1 = box_to_px(bb, ox, oy)
                symbols.append({'cls': ccls, 'cx': 0.5 * (x0 + x1), 'cy': 0.5 * (y0 + y1), 'box': (x0, y0, x1, y1)})

        if cls == 'dots':
            bb = _direct_bbox(el)
            if bb:
                x0, y0, x1, y1 = box_to_px(bb, ox, oy)
                symbols.append({'cls': 'dot', 'cx': 0.5 * (x0 + x1), 'cy': 0.5 * (y0 + y1), 'box': (x0, y0, x1, y1)})

        if cls == 'dynam':
            bb = _direct_bbox(el)
            if bb:
                x0, y0, x1, y1 = box_to_px(bb, ox, oy)
                symbols.append({'cls': 'dynamic', 'cx': 0.5 * (x0 + x1), 'cy': 0.5 * (y0 + y1), 'box': (x0, y0, x1, y1)})

        if cls == 'fermata':
            bb = _direct_bbox(el)
            if bb:
                x0, y0, x1, y1 = box_to_px(bb, ox, oy)
                symbols.append({'cls': 'fermata', 'cx': 0.5 * (x0 + x1), 'cy': 0.5 * (y0 + y1), 'box': (x0, y0, x1, y1)})

        if cls == 'meterSig':
            bb = _direct_bbox(el)
            if bb:
                x0, y0, x1, y1 = box_to_px(bb, ox, oy)
                sym = el.attrib.get('data-sym')
                cnt = el.attrib.get('data-count')
                unit = el.attrib.get('data-unit')
                meters.append({'box': (x0, y0, x1, y1), 'sym': sym, 'count': cnt, 'unit': unit})
                # Time-signature digits also serve as hard negatives for SymNet 'noise'.
                negatives.append({'kind': 'time_digit', 'cx': 0.5 * (x0 + x1), 'cy': y0 + 0.25 * (y1 - y0)})
                negatives.append({'kind': 'time_digit', 'cx': 0.5 * (x0 + x1), 'cy': y0 + 0.75 * (y1 - y0)})

        if cls in ('barLine', 'slur', 'tie', 'beam', 'flag', 'text'):
            bb = _direct_bbox(el)
            if bb:
                x0, y0, x1, y1 = box_to_px(bb, ox, oy)
                if (x1 - x0) >= 1.0 and (y1 - y0) >= 2.0:
                    negatives.append({'kind': cls, 'cx': 0.5 * (x0 + x1), 'cy': 0.5 * (y0 + y1)})

        for child in el:
            walk(child, ox, oy, cur_sys, cur_staff_rows, cur_chord_dur)

    walk(def_svg, 0.0, 0.0, -1, None, None)

    # Sort staves top-to-bottom within each system and build scorereader places.
    places: list[dict] = []
    flat_staves: list[dict] = []
    for sys_idx, st_list in enumerate(systems_staves):
        if not st_list:
            continue
        st_list.sort(key=lambda s: s['rows'][0])
        sp = float(np.median([s['space'] for s in st_list]))
        top = max(0, int(round(st_list[0]['rows'][0] - 4.0 * sp)))
        bottom = min(png_h, int(round(st_list[-1]['rows'][4] + 4.5 * sp)))
        left = max(0, int(round(min(s['x0'] for s in st_list) - 0.8 * sp)))
        st_indices = []
        for s in st_list:
            st_indices.append(len(flat_staves))
            flat_staves.append(s)
        places.append({
            'top': top,
            'bottom': bottom,
            'left': left,
            'staves': st_indices,
            'lines': [[round(r, 1) for r in s['rows']] for s in st_list],
            'x': [[int(round(s['x0'])), int(round(s['x1']))] for s in st_list],
        })

    return {
        'places': places,
        'symbols': symbols,
        'stems': stems,
        'meters': meters,
        'negatives': negatives,
    }


def apply_scan_degradation(grey: np.ndarray, mode: str, rng: np.random.Generator,
                           staves_rows: list[list[float]] | None = None) -> np.ndarray:
    """Applies realistic print and scanner degradations to a full rendered music page."""
    if mode == 'clean':
        return grey.copy()

    out = grey.astype(np.float32)
    h, w = out.shape

    if mode == 'bleed':
        k = int(rng.choice([2, 3]))
        out = cv2.erode(out, np.ones((k, k), np.uint8))
        out = cv2.GaussianBlur(out, (0, 0), float(rng.uniform(0.55, 1.15)))
    elif mode == 'faint':
        if rng.random() < 0.65:
            out = cv2.dilate(out, np.ones((2, 2), np.uint8))
        out = cv2.GaussianBlur(out, (0, 0), float(rng.uniform(0.35, 0.85)))
        dark = float(rng.uniform(45.0, 95.0))
        paper = float(rng.uniform(232.0, 255.0))
        out = dark + (out / 255.0) * (paper - dark)
    elif mode == 'pinholes':
        # Random white toner pinholes strictly inside dark ink pixels.
        dark_mask = out < 120.0
        ys, xs = np.nonzero(dark_mask)
        if len(ys) > 20:
            n_holes = min(len(ys) // 35, int(rng.integers(400, 1800)))
            pick = rng.choice(len(ys), size=max(1, n_holes), replace=False)
            for idx in pick:
                r = int(rng.choice([1, 1, 2]))
                cv2.circle(out, (int(xs[idx]), int(ys[idx])), r, float(rng.uniform(175.0, 245.0)), -1)
        out = cv2.GaussianBlur(out, (0, 0), float(rng.uniform(0.35, 0.75)))
    elif mode == 'staff_cuts':
        # Faint or broken staff-line cuts plus mild blur.
        if staves_rows:
            for rows in staves_rows:
                for row in rows:
                    ry = int(round(row))
                    if 1 <= ry < h - 1:
                        # Punch short random horizontal dropouts along staff lines.
                        for _ in range(18):
                            x0 = int(rng.integers(0, max(1, w - 40)))
                            seg = int(rng.integers(10, 45))
                            out[ry - 1:ry + 2, x0:min(w, x0 + seg)] = np.maximum(
                                out[ry - 1:ry + 2, x0:min(w, x0 + seg)],
                                float(rng.uniform(140.0, 235.0)),
                            )
        out = cv2.GaussianBlur(out, (0, 0), float(rng.uniform(0.40, 0.90)))
    elif mode == 'skew_resample':
        # Simulate slight scan skew and deskew resampling blur (+-0.25 deg residual).
        ang1 = float(rng.choice([-1.0, 1.0]) * rng.uniform(0.5, 1.1))
        ang2 = -ang1 + float(rng.uniform(-0.18, 0.18))
        m1 = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), ang1, 1.0)
        m2 = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), ang2, 1.0)
        tmp = cv2.warpAffine(out, m1, (w, h), flags=cv2.INTER_CUBIC, borderValue=255.0)
        out = cv2.warpAffine(tmp, m2, (w, h), flags=cv2.INTER_CUBIC, borderValue=255.0)
    else:
        # Mild combined scan copy.
        out = cv2.GaussianBlur(out, (0, 0), float(rng.uniform(0.4, 0.8)))

    if mode != 'faint':
        dark = float(rng.uniform(0.0, 42.0))
        paper = float(rng.uniform(225.0, 255.0))
        out = dark + (out / 255.0) * (paper - dark)
    noise = rng.normal(0.0, float(rng.uniform(1.5, 6.5)), out.shape)
    return np.clip(out + noise, 0.0, 255.0).astype(np.uint8)


def _bridge_staff_rows_only(mask: np.ndarray, row_positions: list[float], thick: float) -> np.ndarray:
    """Bridges vertical breaks only inside narrow bands around staff rows (matches meter.py)."""
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


def _nearest_staff(staves: list[dict], cx: float, cy: float) -> int | None:
    """Finds the nearest staff index for a page point (cx, cy)."""
    best_i = None
    best_d = 1e9
    for idx, st in enumerate(staves):
        d = abs(cy - st['rows'][2])
        if d < best_d:
            best_d = d
            best_i = idx
    if best_i is None:
        return None
    sp = float(staves[best_i]['space'])
    if best_d > 7.5 * sp:
        return None
    return best_i


def _refine_center_on_bare(bare: np.ndarray, cx: float, cy: float, sp: float) -> tuple[float, float]:
    """Refines a key-accidental glyph center to the tight bare-ink bbox center inside a local window."""
    h, w = bare.shape
    rad_x = int(round(0.70 * sp))
    rad_y = int(round(1.45 * sp))
    x0, x1 = max(0, int(round(cx)) - rad_x), min(w, int(round(cx)) + rad_x + 1)
    y0, y1 = max(0, int(round(cy)) - rad_y), min(h, int(round(cy)) + rad_y + 1)
    if x1 <= x0 or y1 <= y0:
        return cx, cy
    sub = bare[y0:y1, x0:x1]
    ys, xs = np.nonzero(sub > 0)
    if len(ys) < 8:
        return cx, cy
    return x0 + 0.5 * (float(xs.min()) + float(xs.max())), y0 + 0.5 * (float(ys.min()) + float(ys.max()))


def _generate_one_page(task: tuple[str, str, int, str, int]) -> dict[str, Any]:
    """Renders one Verovio score page, degrades it, runs read_layers(), and extracts all 3 crop sets."""
    cv2.setNumThreads(1)
    font_name, template_name, variant_idx, deg_mode, seed = task
    rng = np.random.default_rng(seed)

    builder = dict(TEMPLATES)[template_name]
    mxml = builder(rng)

    verovio.enableLog(verovio.LOG_OFF)
    tk = verovio.toolkit()
    scale_opt = int(rng.integers(36, 45))
    page_w_mm = 2100
    page_h_mm = 2970
    tk.setOptions({
        'font': font_name,
        'scale': scale_opt,
        'pageWidth': page_w_mm,
        'pageHeight': page_h_mm,
        'adjustPageHeight': True,
        'footer': 'none',
        'header': 'none',
        'staffLineWidth': round(float(rng.uniform(0.11, 0.22)), 3),
        'stemWidth': round(float(rng.uniform(0.10, 0.16)), 3),
        'spacingStaff': int(rng.integers(7, 13)),
        'svgBoundingBoxes': True,
        'svgViewBox': True,
        'svgAdditionalAttribute': [
            'note@dur', 'chord@dur', 'rest@dur', 'mRest@dur',
            'accid@accid', 'clef@shape',
            'meterSig@count', 'meterSig@unit', 'meterSig@sym',
            'stem@dir',
        ],
    })
    tk.loadData(mxml)
    if tk.getPageCount() < 1:
        return {'sym': ([], [], [], []), 'stem': ([], [], [], []), 'time': ([], [], [], []), 'ink_checks': []}

    svg = tk.renderToSVG(1)
    width_px = int(rng.choice([2100, 2320, 2480, 2650]))
    clean_grey = _render_svg_to_grey(svg, width_px)
    png_h, png_w = clean_grey.shape

    ann = _extract_svg_annotations(svg, png_w, png_h)
    places = ann['places']
    if not places:
        return {'sym': ([], [], [], []), 'stem': ([], [], [], []), 'time': ([], [], [], []), 'ink_checks': []}

    all_rows = [rows for p in places for rows in p['lines']]
    grey = apply_scan_degradation(clean_grey, deg_mode, rng, staves_rows=all_rows)
    layers = read_layers(grey, places)
    bare = layers['bare']
    staves = layers['staves']
    levels = page_levels(grey)
    free = _free(layers)

    group_id = f'{font_name}/{template_name}_v{variant_idx}_{deg_mode}'

    sym_x, sym_y, sym_g, sym_f = [], [], [], []
    stem_x, stem_y, stem_g, stem_f = [], [], [], []
    time_x, time_y, time_g, time_f = [], [], [], []
    ink_checks: list[tuple[str, float]] = []

    occupied: list[tuple[float, float, float, float]] = []

    # 1. SymNet symbol patches (18 positive classes)
    for sym in ann['symbols']:
        cls_name = sym['cls']
        si = _nearest_staff(staves, sym['cx'], sym['cy'])
        if si is None:
            continue
        staff = staves[si]
        sp = float(staff['space'])
        cx, cy = float(sym['cx']), float(sym['cy'])
        if sym.get('refine'):
            cx, cy = _refine_center_on_bare(bare, cx, cy, sp)
        if sym['box'] is not None:
            occupied.append(sym['box'])
        else:
            occupied.append((cx - 0.5 * sp, cy - 1.0 * sp, cx + 0.5 * sp, cy + 1.0 * sp))

        # Slight realistic center jitter (+/- 0.08*sp) matching real candidate detectors.
        jx = cx + float(rng.uniform(-0.08, 0.08) * sp)
        jy = cy + float(rng.uniform(-0.08, 0.08) * sp)
        patch = extract_patch(grey, bare, staff['rows'], sp, jx, jy, size=PATCH_SIZE, levels=levels)
        # Validate central ink density on clean and degraded crops for alignment telemetry.
        center_ink = float(patch[0, 10:22, 10:22].mean())
        if center_ink < 0.015:
            continue
        ink_checks.append((cls_name, center_ink))
        sym_x.append((patch * 255.0).round().astype(np.uint8))
        sym_y.append(CLASS_TO_ID[cls_name])
        sym_g.append(group_id)
        sym_f.append(font_name)

        # Also harvest a few TimeNet 'other' negatives from real accidentals/rests/clefs/heads.
        if cls_name in ('acc_sharp', 'acc_flat', 'acc_natural', 'rest_quarter', 'rest_eighth', 'clef_G', 'clef_F') and rng.random() < 0.12:
            if sym['box'] is not None:
                bx0, by0, bx1, by1 = sym['box']
                ix0, iy0 = max(0, int(bx0) - 1), max(0, int(by0) - 1)
                ix1, iy1 = min(png_w, int(bx1) + 2), min(png_h, int(by1) + 2)
                if ix1 > ix0 + 3 and iy1 > iy0 + 3:
                    sub = free[iy0:iy1, ix0:ix1].astype(np.float32)
                    ynz, xnz = np.nonzero(sub > 0.15)
                    if len(ynz) >= 8:
                        time_x.append(_normalize_time_crop(sub[ynz.min():ynz.max() + 1, xnz.min():xnz.max() + 1]))
                        time_y.append(TIME_TO_ID['other'])
                        time_g.append(group_id)
                        time_f.append(font_name)

    # 2. SymNet 'noise' hard negatives (barlines, slurs, ties, beams, flag tips, lyrics, time digits, down-stem necks, off-center heads)
    neg_pts: list[tuple[float, float]] = [(n['cx'], n['cy']) for n in ann['negatives']]
    # Add off-center head shifts (1.25..1.55 sp away from real noteheads)
    head_syms = [s for s in ann['symbols'] if s['cls'].startswith('head_')]
    if head_syms:
        pick_n = min(14, len(head_syms))
        for idx in rng.choice(len(head_syms), size=pick_n, replace=False):
            hs = head_syms[int(idx)]
            si = _nearest_staff(staves, hs['cx'], hs['cy'])
            if si is not None:
                sp = float(staves[si]['space'])
                ang = float(rng.uniform(0.0, 2.0 * np.pi))
                dist = float(rng.uniform(1.25, 1.55) * sp)
                neg_pts.append((hs['cx'] + dist * np.cos(ang), hs['cy'] + dist * np.sin(ang)))
    # Add a few blank staff-line regions
    for st in staves:
        for _ in range(2):
            rx = float(rng.uniform(st['x0'] + 4.0 * st['space'], max(st['x0'] + 5.0 * st['space'], st['x1'] - 2.0 * st['space'])))
            ry = float(st['rows'][2] + rng.uniform(-1.5, 1.5) * st['space'])
            neg_pts.append((rx, ry))

    rng.shuffle(neg_pts)
    kept_neg = 0
    max_neg = 42
    for nx, ny in neg_pts:
        if kept_neg >= max_neg:
            break
        si = _nearest_staff(staves, nx, ny)
        if si is None:
            continue
        staff = staves[si]
        sp = float(staff['space'])
        # Ensure negative center does not land inside any real symbol box.
        if any(x0 - 0.35 * sp <= nx <= x1 + 0.35 * sp and y0 - 0.35 * sp <= ny <= y1 + 0.35 * sp
               for x0, y0, x1, y1 in occupied):
            continue
        patch = extract_patch(grey, bare, staff['rows'], sp, nx, ny, size=PATCH_SIZE, levels=levels)
        sym_x.append((patch * 255.0).round().astype(np.uint8))
        sym_y.append(CLASS_TO_ID['noise'])
        sym_g.append(group_id)
        sym_f.append(font_name)
        kept_neg += 1

    # 3. StemNet canonical stem-tip patches (3, 32, 32), 4.5 spaces, down-stems flipped up
    for st_item in ann['stems']:
        sx, send = float(st_item['x']), float(st_item['end'])
        si = _nearest_staff(staves, sx, send)
        if si is None:
            continue
        staff = staves[si]
        sp = float(staff['space'])
        jx = sx + float(rng.uniform(-0.10, 0.10) * sp)
        jy = send + float(rng.uniform(-0.10, 0.10) * sp)
        patch = extract_patch(grey, bare, staff['rows'], sp, jx, jy, size=STEM_SIZE, spaces=STEM_SPACES, levels=levels)
        if st_item['dir'] == 'down':
            patch = patch[:, ::-1, :].copy()
        stem_x.append((patch * 255.0).round().astype(np.uint8))
        stem_y.append(int(st_item['tails']))
        stem_g.append(group_id)
        stem_f.append(font_name)

    # 4. TimeNet meter glyph patches (1, 24, 24) with staff-row-only bridging
    for mt in ann['meters']:
        mx0, my0, mx1, my1 = mt['box']
        mcx, mcy = 0.5 * (mx0 + mx1), 0.5 * (my0 + my1)
        si = _nearest_staff(staves, mcx, mcy)
        if si is None:
            continue
        staff = staves[si]
        sp = float(staff['space'])
        rows = staff['rows']
        thick = float(staff['thick'])
        sym_tag = mt.get('sym')
        if sym_tag in ('common', 'cut'):
            lbl = 'cut' if sym_tag == 'cut' else 'C'
            x0 = max(0, int(mx0) - 2)
            x1 = min(png_w, int(mx1) + 3)
            y0 = max(0, int(rows[0] - 0.65 * sp))
            y1 = min(png_h, int(rows[4] + 0.65 * sp) + 1)
            if x1 > x0 + 3 and y1 > y0 + 3:
                sub = _bridge_staff_rows_only(free[y0:y1, x0:x1], [r - y0 for r in rows], thick)
                ynz, xnz = np.nonzero(sub)
                if len(ynz) >= 8:
                    time_x.append(_normalize_time_crop(sub[ynz.min():ynz.max() + 1, xnz.min():xnz.max() + 1].astype(np.float32)))
                    time_y.append(TIME_TO_ID[lbl])
                    time_g.append(group_id)
                    time_f.append(font_name)
        else:
            cnt_s, unit_s = str(mt.get('count') or ''), str(mt.get('unit') or '')
            x0 = max(0, int(mx0) - 2)
            x1 = min(png_w, int(mx1) + 3)
            y_top = max(0, int(rows[0] - 0.35 * sp))
            y_mid = int(round(rows[2]))
            y_bot = min(png_h, int(rows[4] + 0.35 * sp) + 1)
            if x1 > x0 + 3 and y_mid > y_top + 3 and y_bot > y_mid + 3:
                for lbl_s, m_raw, y_off in ((cnt_s, free[y_top:y_mid, x0:x1], y_top),
                                            (unit_s, free[y_mid:y_bot, x0:x1], y_mid)):
                    if lbl_s not in TIME_TO_ID:
                        continue
                    sub = _bridge_staff_rows_only(m_raw, [r - y_off for r in rows], thick)
                    ynz, xnz = np.nonzero(sub)
                    if len(ynz) >= 8:
                        time_x.append(_normalize_time_crop(sub[ynz.min():ynz.max() + 1, xnz.min():xnz.max() + 1].astype(np.float32)))
                        time_y.append(TIME_TO_ID[lbl_s])
                        time_g.append(group_id)
                        time_f.append(font_name)

    return {
        'sym': (sym_x, sym_y, sym_g, sym_f),
        'stem': (stem_x, stem_y, stem_g, stem_f),
        'time': (time_x, time_y, time_g, time_f),
        'ink_checks': ink_checks,
    }


def _save_contact_sheet(X: np.ndarray, Y: np.ndarray, class_names: tuple[str, ...], out_png: Path) -> None:
    """Writes a compact visual contact sheet (one row per class) to verify crop alignment."""
    cols = 10
    rows = len(class_names)
    cell = X.shape[-1]
    pad = 2
    label_w = 105
    h = rows * (cell + pad) + pad
    w = label_w + cols * (cell + pad) + pad
    canvas = np.full((h, w, 3), 240, dtype=np.uint8)
    for cid, cname in enumerate(class_names):
        y0 = pad + cid * (cell + pad)
        cv2.putText(canvas, cname[:13], (4, y0 + cell - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (20, 20, 20), 1, cv2.LINE_AA)
        idxs = np.where(Y == cid)[0]
        if len(idxs) == 0:
            continue
        step = max(1, len(idxs) // cols)
        chosen = idxs[::step][:cols]
        for j, idx in enumerate(chosen):
            x0 = label_w + pad + j * (cell + pad)
            patch = X[idx]
            if patch.shape[0] == 3:
                # Render ch0 (grey ink), ch1 (bare ink), ch2 (staff lines) into a clear BGR preview.
                img = np.full((cell, cell, 3), 255, dtype=np.uint8)
                g_ink = patch[0].astype(np.float32) / 255.0
                b_ink = patch[1].astype(np.float32) / 255.0
                s_lin = patch[2].astype(np.float32) / 255.0
                img[:, :, 0] = np.clip(255.0 * (1.0 - 0.85 * g_ink - 0.15 * b_ink), 0, 255).astype(np.uint8)
                img[:, :, 1] = np.clip(255.0 * (1.0 - 0.85 * g_ink - 0.25 * s_lin), 0, 255).astype(np.uint8)
                img[:, :, 2] = np.clip(255.0 * (1.0 - 0.90 * b_ink - 0.30 * g_ink), 0, 255).astype(np.uint8)
            else:
                v = 255 - patch[0]
                img = np.stack([v, v, v], axis=-1)
            canvas[y0:y0 + cell, x0:x0 + cell] = img
    out_png.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_png), canvas)


def validate_crops(sym_path: Path, stem_path: Path, time_path: Path, preview_dir: Path | None = None) -> dict[str, Any]:
    """Runs statistical alignment and coverage validation on the three generated NPZ datasets."""
    report: dict[str, Any] = {}
    for key, path, expected_shape, expected_classes in (
        ('sym', sym_path, (3, PATCH_SIZE, PATCH_SIZE), CLASSES),
        ('stem', stem_path, (3, STEM_SIZE, STEM_SIZE), STEM_CLASSES),
        ('time', time_path, (1, TIME_SIZE, TIME_SIZE), TIME_CLASSES),
    ):
        d = np.load(path)
        X, Y, F = d['X'], d['Y'], d['F']
        assert X.ndim == 4 and X.shape[1:] == expected_shape and X.dtype == np.uint8, f'{key} bad shape: {X.shape}'
        assert len(X) == len(Y) == len(F), f'{key} length mismatch'
        counts = {expected_classes[c]: int((Y == c).sum()) for c in range(len(expected_classes))}
        missing = [k for k, v in counts.items() if v == 0]
        # Check center-window mean ink across positive classes to confirm pixel alignment.
        c_slice = slice(8, 24) if expected_shape[1] == 32 else slice(4, 20)
        center_means = X[:, 0, c_slice, c_slice].mean(axis=(1, 2)) / 255.0
        zero_ink_frac = float((center_means < 0.01).mean()) if len(X) else 1.0
        fonts = dict(Counter(F.tolist()))
        report[key] = {
            'total': int(len(Y)),
            'missing_classes': missing,
            'min_class_count': min(counts.values()) if counts else 0,
            'center_ink_mean': round(float(center_means.mean()), 4) if len(X) else 0.0,
            'zero_ink_frac': round(zero_ink_frac, 4),
            'counts': counts,
            'fonts': fonts,
        }
        if preview_dir is not None and len(X):
            _save_contact_sheet(X, Y, expected_classes, preview_dir / f'verovio_{key}_preview.png')
    return report


def generate_datasets(
    out_dir: Path,
    fonts: tuple[str, ...] = SMUFL_FONTS,
    variants: int = 3,
    workers: int = 8,
    seed: int = 2026,
    preview_dir: Path | None = None,
) -> dict[str, Any]:
    """Generates SymNet, StemNet, and TimeNet Verovio datasets across all fonts and scan modes."""
    t0 = time.time()
    deg_modes = ('clean', 'bleed', 'faint', 'pinholes', 'staff_cuts', 'skew_resample')
    tasks: list[tuple[str, str, int, str, int]] = []
    idx = 0
    for font in fonts:
        for tname, _ in TEMPLATES:
            for v in range(variants):
                mode = deg_modes[(idx + v) % len(deg_modes)]
                tasks.append((font, tname, v, mode, seed + idx * 97 + v * 13))
                idx += 1

    sym_x, sym_y, sym_g, sym_f = [], [], [], []
    stem_x, stem_y, stem_g, stem_f = [], [], [], []
    time_x, time_y, time_g, time_f = [], [], [], []

    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            for res in pool.map(_generate_one_page, tasks):
                sx, sy, sg, sf = res['sym']
                sym_x.extend(sx); sym_y.extend(sy); sym_g.extend(sg); sym_f.extend(sf)
                tx, ty, tg, tf = res['stem']
                stem_x.extend(tx); stem_y.extend(ty); stem_g.extend(tg); stem_f.extend(tf)
                mx, my, mg, mf = res['time']
                time_x.extend(mx); time_y.extend(my); time_g.extend(mg); time_f.extend(mf)
    else:
        for task in tasks:
            res = _generate_one_page(task)
            sx, sy, sg, sf = res['sym']
            sym_x.extend(sx); sym_y.extend(sy); sym_g.extend(sg); sym_f.extend(sf)
            tx, ty, tg, tf = res['stem']
            stem_x.extend(tx); stem_y.extend(ty); stem_g.extend(tg); stem_f.extend(tf)
            mx, my, mg, mf = res['time']
            time_x.extend(mx); time_y.extend(my); time_g.extend(mg); time_f.extend(mf)

    out_dir.mkdir(parents=True, exist_ok=True)
    sym_path = out_dir / 'verovio_synth_crops.npz'
    stem_path = out_dir / 'verovio_stem_crops.npz'
    time_path = out_dir / 'verovio_time_crops.npz'

    np.savez_compressed(
        sym_path,
        X=np.stack(sym_x, axis=0) if sym_x else np.zeros((0, 3, PATCH_SIZE, PATCH_SIZE), np.uint8),
        Y=np.array(sym_y, dtype=np.int16),
        G=np.array(sym_g),
        F=np.array(sym_f),
        classes=np.array(CLASSES),
    )
    np.savez_compressed(
        stem_path,
        X=np.stack(stem_x, axis=0) if stem_x else np.zeros((0, 3, STEM_SIZE, STEM_SIZE), np.uint8),
        Y=np.array(stem_y, dtype=np.int64),
        G=np.array(stem_g),
        F=np.array(stem_f),
        classes=np.array(STEM_CLASSES),
    )
    np.savez_compressed(
        time_path,
        X=np.stack(time_x, axis=0) if time_x else np.zeros((0, 1, TIME_SIZE, TIME_SIZE), np.uint8),
        Y=np.array(time_y, dtype=np.int64),
        G=np.array(time_g),
        F=np.array(time_f),
        classes=np.array(TIME_CLASSES),
    )
    elapsed = time.time() - t0
    val = validate_crops(sym_path, stem_path, time_path, preview_dir=preview_dir)
    val['elapsed_sec'] = round(elapsed, 2)
    val['pages_rendered'] = len(tasks)
    val['paths'] = {
        'sym': str(sym_path),
        'stem': str(stem_path),
        'time': str(time_path),
    }
    return val


def main() -> int:
    parser = argparse.ArgumentParser(description='Generate multi-font Verovio engraved training crops.')
    parser.add_argument('--out-dir', default='/tmp/scorereader_swarm', help='Directory for output .npz datasets')
    parser.add_argument('--preview-dir', default='/tmp/scorereader_swarm/omr_eval', help='Directory for contact-sheet PNG previews')
    parser.add_argument('--variants', type=int, default=3, help='Page variants per (font, template) pair')
    parser.add_argument('--workers', type=int, default=8, help='Parallel worker processes')
    parser.add_argument('--seed', type=int, default=2026, help='Random seed')
    args = parser.parse_args()

    os.environ.setdefault('OMP_NUM_THREADS', '1')
    os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
    report = generate_datasets(
        Path(args.out_dir),
        variants=args.variants,
        workers=args.workers,
        seed=args.seed,
        preview_dir=Path(args.preview_dir) if args.preview_dir else None,
    )
    print(f"Generated {report['pages_rendered']} Verovio pages across 5 SMuFL fonts in {report['elapsed_sec']:.1f}s:")
    for key in ('sym', 'stem', 'time'):
        info = report[key]
        print(f"\n[{key}] {info['total']} crops -> {report['paths'][key]}")
        print(f"  center_ink_mean={info['center_ink_mean']:.4f} zero_ink_frac={info['zero_ink_frac']:.4f} missing={info['missing_classes']}")
        print(f"  fonts={info['fonts']}")
        for cname, cnt in info['counts'].items():
            print(f"    {cname:14s}: {cnt:5d}")
    return 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""Programmatic Verovio multi-font round-trip benchmark for ScoreReader.

Generates a 100%-exact ground-truth MusicXML suite covering SATB hymns, 1-staff and
2-staff chant, all meters (2/2, 2/4, 3/4, 4/4, 3/2, 6/8, C, C|, plus mid-staff
changes), all rest types (whole/half/quarter/eighth/16th, dotted, stacked multi-voice,
anacrusis), accidentals, barline-tied accidentals, sharp/flat key signatures, ledger
lines, beamed eighths/16ths, dots, ties, triplets, and divisi 2nd/3rd chords.

Renders each score with Verovio across 5 SMuFL fonts (Leipzig, Bravura, Petaluma,
Leland, Gootville) via /usr/bin/rsvg-convert at 300 DPI (clean + mild scan-degraded),
runs ScoreReader on the PNGs, and evaluates exact round-trip Note F1, Rest F1,
Onset Exact %, and Meter accuracy using bench/eval_f1.py helpers.

Usage:
  PYTHONDONTWRITEBYTECODE=1 out/tools/omr-bench/verovio-venv/bin/python bench/test_verovio_roundtrip.py
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import verovio

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bench.eval_f1 import (
    align_notes,
    align_rests,
    join_ties,
    match_staves,
    norm_meter,
    prf,
    read_musicxml,
    reader_tokens,
    split_by_clef,
    split_parts,
    tally_pairs,
)
from scorereader.page import clean_page, flat_paper
from scorereader.reader import read_page
from scorereader.staves import find_staves
from scorereader.systems import find_systems, lost_staves

SMUFL_FONTS = ('Leipzig', 'Bravura', 'Petaluma', 'Leland', 'Gootville')
RSVG_CONVERT = '/usr/bin/rsvg-convert'
TMP_OUT = Path('/tmp/scorereader_swarm/omr_eval/verovio_roundtrip')


# ---------------------------------------------------------------------------
# Programmatic MusicXML builders
# ---------------------------------------------------------------------------

def _n(
    step: str,
    octave: int,
    dur: int,
    ntype: str,
    *,
    alter: int = 0,
    acc: str | None = None,
    dot: bool = False,
    stem: str | None = None,
    voice: int = 1,
    staff: int = 1,
    chord: bool = False,
    beam1: str | None = None,
    beam2: str | None = None,
    tie: str | None = None,
    tuplet: str | None = None,
    time_mod: tuple[int, int] | None = None,
    lyric: str | None = None,
) -> str:
    parts = ['<note>']
    if chord:
        parts.append('<chord/>')
    alt = f'<alter>{alter}</alter>' if alter != 0 else ''
    parts.append(f'<pitch><step>{step}</step>{alt}<octave>{octave}</octave></pitch>')
    parts.append(f'<duration>{dur}</duration>')
    if tie in ('start', 'stop'):
        parts.append(f'<tie type="{tie}"/>')
    elif tie == 'both':
        parts.append('<tie type="stop"/><tie type="start"/>')
    parts.append(f'<voice>{voice}</voice>')
    parts.append(f'<type>{ntype}</type>')
    if dot:
        parts.append('<dot/>')
    if acc:
        parts.append(f'<accidental>{acc}</accidental>')
    if time_mod:
        parts.append(f'<time-modification><actual-notes>{time_mod[0]}</actual-notes><normal-notes>{time_mod[1]}</normal-notes></time-modification>')
    if stem:
        parts.append(f'<stem>{stem}</stem>')
    parts.append(f'<staff>{staff}</staff>')
    if beam1:
        parts.append(f'<beam number="1">{beam1}</beam>')
    if beam2:
        parts.append(f'<beam number="2">{beam2}</beam>')
    notations = []
    if tie in ('start', 'stop'):
        notations.append(f'<tied type="{tie}"/>')
    elif tie == 'both':
        notations.append('<tied type="stop"/><tied type="start"/>')
    if tuplet in ('start', 'stop'):
        notations.append(f'<tuplet type="{tuplet}"/>')
    if notations:
        parts.append('<notations>' + ''.join(notations) + '</notations>')
    if lyric:
        parts.append(f'<lyric number="1"><text>{lyric}</text></lyric>')
    parts.append('</note>')
    return ''.join(parts)


def _r(
    dur: int,
    ntype: str | None,
    *,
    voice: int = 1,
    staff: int = 1,
    dot: bool = False,
    measure: bool = False,
    display: tuple[str, int] | None = None,
) -> str:
    parts = ['<note>']
    if measure:
        parts.append('<rest measure="yes"/>')
    elif display:
        parts.append(f'<rest><display-step>{display[0]}</display-step><display-octave>{display[1]}</display-octave></rest>')
    else:
        parts.append('<rest/>')
    parts.append(f'<duration>{dur}</duration>')
    parts.append(f'<voice>{voice}</voice>')
    if ntype:
        parts.append(f'<type>{ntype}</type>')
    if dot:
        parts.append('<dot/>')
    parts.append(f'<staff>{staff}</staff>')
    parts.append('</note>')
    return ''.join(parts)


def _attrs(
    divisions: int | None = None,
    fifths: int | None = None,
    time_sig: tuple[int, int, str | None] | None = None,
    staves: int | None = None,
    clefs: list[tuple[int, str, int] | tuple[int, str, int, int]] | None = None,
) -> str:
    parts = ['<attributes>']
    if divisions is not None:
        parts.append(f'<divisions>{divisions}</divisions>')
    if fifths is not None:
        parts.append(f'<key><fifths>{fifths}</fifths></key>')
    if time_sig is not None:
        b, bt, sym = time_sig
        sa = f' symbol="{sym}"' if sym else ''
        parts.append(f'<time{sa}><beats>{b}</beats><beat-type>{bt}</beat-type></time>')
    if staves is not None:
        parts.append(f'<staves>{staves}</staves>')
    for clef_spec in (clefs or []):
        num, sign, line = clef_spec[0], clef_spec[1], clef_spec[2]
        oct_chg = clef_spec[3] if len(clef_spec) > 3 else 0
        oct_xml = f'<clef-octave-change>{oct_chg}</clef-octave-change>' if oct_chg else ''
        parts.append(f'<clef number="{num}"><sign>{sign}</sign><line>{line}</line>{oct_xml}</clef>')
    parts.append('</attributes>')
    return ''.join(parts)


def _wrap(measures: list[str], title: str) -> str:
    body = ''.join(f'<measure number="{i}">{m}</measure>' for i, m in enumerate(measures, 1))
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<score-partwise version="3.1">'
        f'<work><work-title>{title}</work-title></work>'
        '<part-list><score-part id="P1"><part-name></part-name></score-part></part-list>'
        f'<part id="P1">{body}</part>'
        '</score-partwise>'
    )


def _satb_bar(
    s_notes: list[str],
    a_notes: list[str],
    t_notes: list[str],
    b_notes: list[str],
    bar_dur: int,
    prefix: str = '',
) -> str:
    return (
        prefix
        + ''.join(s_notes)
        + f'<backup><duration>{bar_dur}</duration></backup>'
        + ''.join(a_notes)
        + f'<backup><duration>{bar_dur}</duration></backup>'
        + ''.join(t_notes)
        + f'<backup><duration>{bar_dur}</duration></backup>'
        + ''.join(b_notes)
    )


def build_roundtrip_suite() -> list[dict[str, Any]]:
    """Builds the 12-case programmatic ground-truth MusicXML benchmark suite."""
    cases: list[dict[str, Any]] = []

    # 1. SATB 4-part hymn in D major (+2 sharps), 4/4, ties across barline, 2nd/3rd chords
    m1 = [
        _satb_bar(
            [_n('F', 5, 4, 'quarter', alter=1, stem='up', voice=1, staff=1),
             _n('E', 5, 4, 'quarter', stem='up', voice=1, staff=1),
             _n('D', 5, 8, 'half', stem='up', voice=1, staff=1)],
            [_n('A', 4, 4, 'quarter', stem='down', voice=2, staff=1),
             _n('G', 4, 4, 'quarter', stem='down', voice=2, staff=1),
             _n('F', 4, 8, 'half', alter=1, stem='down', voice=2, staff=1)],
            [_n('D', 4, 4, 'quarter', stem='up', voice=5, staff=2),
             _n('C', 4, 4, 'quarter', alter=1, stem='up', voice=5, staff=2),
             _n('A', 3, 8, 'half', stem='up', voice=5, staff=2)],
            [_n('D', 3, 4, 'quarter', stem='down', voice=6, staff=2),
             _n('A', 2, 4, 'quarter', stem='down', voice=6, staff=2),
             _n('D', 3, 8, 'half', stem='down', voice=6, staff=2)],
            16,
            prefix=_attrs(divisions=4, fifths=2, time_sig=(4, 4, None), staves=2, clefs=[(1, 'G', 2), (2, 'F', 4)]),
        ),
        _satb_bar(
            [_n('G', 5, 4, 'quarter', stem='up', voice=1, staff=1),
             _n('F', 5, 4, 'quarter', alter=1, stem='up', voice=1, staff=1),
             _n('E', 5, 8, 'half', stem='up', voice=1, staff=1, tie='start')],
            [_n('B', 4, 4, 'quarter', stem='down', voice=2, staff=1),
             _n('A', 4, 4, 'quarter', stem='down', voice=2, staff=1),
             _n('A', 4, 8, 'half', stem='down', voice=2, staff=1)],
            [_n('D', 4, 4, 'quarter', stem='up', voice=5, staff=2),
             _n('D', 4, 4, 'quarter', stem='up', voice=5, staff=2),
             _n('C', 4, 8, 'half', alter=1, stem='up', voice=5, staff=2)],
            [_n('G', 3, 4, 'quarter', stem='down', voice=6, staff=2),
             _n('D', 3, 4, 'quarter', stem='down', voice=6, staff=2),
             _n('A', 2, 8, 'half', stem='down', voice=6, staff=2)],
            16,
        ),
        _satb_bar(
            [_n('E', 5, 4, 'quarter', stem='up', voice=1, staff=1, tie='stop'),
             _n('D', 5, 4, 'quarter', stem='up', voice=1, staff=1),
             _n('C', 5, 4, 'quarter', alter=1, stem='up', voice=1, staff=1),
             _n('D', 5, 4, 'quarter', stem='up', voice=1, staff=1)],
            [_n('G', 4, 4, 'quarter', stem='down', voice=2, staff=1),
             _n('F', 4, 4, 'quarter', alter=1, stem='down', voice=2, staff=1),
             _n('E', 4, 4, 'quarter', stem='down', voice=2, staff=1),
             _n('F', 4, 4, 'quarter', alter=1, stem='down', voice=2, staff=1)],
            [_n('C', 4, 4, 'quarter', alter=1, stem='up', voice=5, staff=2),
             _n('A', 3, 4, 'quarter', stem='up', voice=5, staff=2),
             _n('A', 3, 4, 'quarter', stem='up', voice=5, staff=2),
             _n('A', 3, 4, 'quarter', stem='up', voice=5, staff=2)],
            [_n('A', 2, 4, 'quarter', stem='down', voice=6, staff=2),
             _n('D', 3, 4, 'quarter', stem='down', voice=6, staff=2),
             _n('A', 2, 4, 'quarter', stem='down', voice=6, staff=2),
             _n('D', 3, 4, 'quarter', stem='down', voice=6, staff=2)],
            16,
        ),
        _satb_bar(
            [_n('D', 5, 16, 'whole', voice=1, staff=1)],
            [_n('F', 4, 16, 'whole', alter=1, voice=2, staff=1)],
            [_n('A', 3, 16, 'whole', voice=5, staff=2)],
            [_n('D', 3, 16, 'whole', voice=6, staff=2)],
            16,
        ),
    ]
    cases.append({
        'id': 'satb_hymn_4_4_sharps',
        'musicxml': _wrap(m1, 'SATB Hymn 4/4 Sharps'),
        'staves': 2,
        'voices_per_staff': [2, 2],
        'features': ['satb', 'meter_4_4', 'keysig_sharps', 'ties'],
    })

    # 2. SATB 4-part hymn in Eb major (-3 flats), 3/4, beamed eighths, dotted quarters, stacked quarter rests, lyrics
    m2 = [
        _satb_bar(
            [_n('G', 4, 6, 'quarter', dot=True, stem='up', voice=1, staff=1, lyric='Lord'),
             _n('A', 4, 2, 'eighth', alter=-1, stem='up', voice=1, staff=1, lyric='have'),
             _n('B', 4, 4, 'quarter', alter=-1, stem='up', voice=1, staff=1, lyric='mer')],
            [_n('E', 4, 8, 'half', alter=-1, stem='down', voice=2, staff=1),
             _n('G', 4, 4, 'quarter', stem='down', voice=2, staff=1)],
            [_n('B', 3, 8, 'half', alter=-1, stem='up', voice=5, staff=2),
             _n('B', 3, 4, 'quarter', alter=-1, stem='up', voice=5, staff=2)],
            [_n('E', 3, 8, 'half', alter=-1, stem='down', voice=6, staff=2),
             _n('E', 3, 4, 'quarter', alter=-1, stem='down', voice=6, staff=2)],
            12,
            prefix=_attrs(divisions=4, fifths=-3, time_sig=(3, 4, None), staves=2, clefs=[(1, 'G', 2), (2, 'F', 4)]),
        ),
        _satb_bar(
            [_n('C', 5, 2, 'eighth', stem='up', voice=1, staff=1, beam1='begin', lyric='cy'),
             _n('B', 4, 2, 'eighth', alter=-1, stem='up', voice=1, staff=1, beam1='end'),
             _n('A', 4, 4, 'quarter', alter=-1, stem='up', voice=1, staff=1, lyric='up'),
             _r(4, 'quarter', voice=1, staff=1, display=('E', 5))],
            [_n('A', 4, 4, 'quarter', alter=-1, stem='down', voice=2, staff=1),
             _n('F', 4, 4, 'quarter', stem='down', voice=2, staff=1),
             _r(4, 'quarter', voice=2, staff=1, display=('E', 4))],
            [_n('E', 4, 4, 'quarter', alter=-1, stem='up', voice=5, staff=2),
             _n('C', 4, 4, 'quarter', stem='up', voice=5, staff=2),
             _r(4, 'quarter', voice=5, staff=2, display=('A', 3))],
            [_n('A', 2, 4, 'quarter', alter=-1, stem='down', voice=6, staff=2),
             _n('F', 2, 4, 'quarter', stem='down', voice=6, staff=2),
             _r(4, 'quarter', voice=6, staff=2, display=('A', 2))],
            12,
        ),
        _satb_bar(
            [_n('B', 4, 4, 'quarter', alter=-1, stem='up', voice=1, staff=1, lyric='on'),
             _n('G', 4, 4, 'quarter', stem='up', voice=1, staff=1, lyric='us'),
             _n('F', 4, 4, 'quarter', stem='up', voice=1, staff=1, lyric='now')],
            [_n('G', 4, 4, 'quarter', stem='down', voice=2, staff=1),
             _n('E', 4, 4, 'quarter', alter=-1, stem='down', voice=2, staff=1),
             _n('D', 4, 4, 'quarter', stem='down', voice=2, staff=1)],
            [_n('B', 3, 4, 'quarter', alter=-1, stem='up', voice=5, staff=2),
             _n('B', 3, 4, 'quarter', alter=-1, stem='up', voice=5, staff=2),
             _n('B', 3, 4, 'quarter', alter=-1, stem='up', voice=5, staff=2)],
            [_n('E', 3, 4, 'quarter', alter=-1, stem='down', voice=6, staff=2),
             _n('E', 3, 4, 'quarter', alter=-1, stem='down', voice=6, staff=2),
             _n('B', 2, 4, 'quarter', alter=-1, stem='down', voice=6, staff=2)],
            12,
        ),
        _satb_bar(
            [_n('E', 4, 12, 'half', alter=-1, dot=True, stem='up', voice=1, staff=1, lyric='men')],
            [_n('E', 4, 12, 'half', alter=-1, dot=True, stem='down', voice=2, staff=1)],
            [_n('G', 3, 12, 'half', dot=True, stem='up', voice=5, staff=2)],
            [_n('E', 3, 12, 'half', alter=-1, dot=True, stem='down', voice=6, staff=2)],
            12,
        ),
    ]
    cases.append({
        'id': 'satb_hymn_3_4_flats',
        'musicxml': _wrap(m2, 'SATB Hymn 3/4 Flats'),
        'staves': 2,
        'voices_per_staff': [2, 2],
        'features': ['satb', 'meter_3_4', 'keysig_flats', 'beamed_8th', 'dots', 'rests_stacked'],
    })

    # 3. SATB Cut time C| -> mid-staff 3/2 -> C common time, with whole & half rests
    m3 = [
        _satb_bar(
            [_n('G', 4, 8, 'half', stem='up', voice=1, staff=1), _n('A', 4, 8, 'half', stem='up', voice=1, staff=1)],
            [_n('E', 4, 8, 'half', stem='down', voice=2, staff=1), _n('F', 4, 8, 'half', stem='down', voice=2, staff=1)],
            [_n('C', 4, 8, 'half', stem='up', voice=5, staff=2), _n('C', 4, 8, 'half', stem='up', voice=5, staff=2)],
            [_n('C', 3, 8, 'half', stem='down', voice=6, staff=2), _n('F', 3, 8, 'half', stem='down', voice=6, staff=2)],
            16,
            prefix=_attrs(divisions=4, fifths=0, time_sig=(2, 2, 'cut'), staves=2, clefs=[(1, 'G', 2), (2, 'F', 4)]),
        ),
        _satb_bar(
            [_n('B', 4, 8, 'half', stem='up', voice=1, staff=1), _r(8, 'half', voice=1, staff=1, display=('F', 5))],
            [_n('G', 4, 8, 'half', stem='down', voice=2, staff=1), _r(8, 'half', voice=2, staff=1, display=('E', 4))],
            [_n('D', 4, 8, 'half', stem='up', voice=5, staff=2), _r(8, 'half', voice=5, staff=2, display=('A', 3))],
            [_n('G', 3, 8, 'half', stem='down', voice=6, staff=2), _r(8, 'half', voice=6, staff=2, display=('G', 2))],
            16,
        ),
        _satb_bar(
            [_n('C', 5, 8, 'half', stem='up', voice=1, staff=1),
             _n('B', 4, 8, 'half', stem='up', voice=1, staff=1),
             _n('A', 4, 8, 'half', stem='up', voice=1, staff=1)],
            [_n('G', 4, 8, 'half', stem='down', voice=2, staff=1),
             _n('G', 4, 8, 'half', stem='down', voice=2, staff=1),
             _n('F', 4, 8, 'half', stem='down', voice=2, staff=1)],
            [_n('E', 4, 8, 'half', stem='up', voice=5, staff=2),
             _n('D', 4, 8, 'half', stem='up', voice=5, staff=2),
             _n('C', 4, 8, 'half', stem='up', voice=5, staff=2)],
            [_n('C', 3, 8, 'half', stem='down', voice=6, staff=2),
             _n('G', 3, 8, 'half', stem='down', voice=6, staff=2),
             _n('F', 3, 8, 'half', stem='down', voice=6, staff=2)],
            24,
            prefix=_attrs(time_sig=(3, 2, None)),
        ),
        _satb_bar(
            [_n('G', 4, 8, 'half', stem='up', voice=1, staff=1), _n('G', 4, 8, 'half', stem='up', voice=1, staff=1)],
            [_n('E', 4, 8, 'half', stem='down', voice=2, staff=1), _n('E', 4, 8, 'half', stem='down', voice=2, staff=1)],
            [_n('C', 4, 8, 'half', stem='up', voice=5, staff=2), _n('C', 4, 8, 'half', stem='up', voice=5, staff=2)],
            [_n('C', 3, 8, 'half', stem='down', voice=6, staff=2), _n('C', 3, 8, 'half', stem='down', voice=6, staff=2)],
            16,
            prefix=_attrs(time_sig=(4, 4, 'common')),
        ),
    ]
    cases.append({
        'id': 'satb_cut_time_midchange',
        'musicxml': _wrap(m3, 'SATB Cut Time Midchange'),
        'staves': 2,
        'voices_per_staff': [2, 2],
        'features': ['satb', 'meter_cut', 'meter_3_2', 'meter_common', 'mid_meter_change', 'rests_whole_half'],
    })

    # 4. 1-staff chant in F major (-1 flat), numeric 2/2, melismas, lyrics
    m4 = [
        _attrs(divisions=4, fifths=-1, time_sig=(2, 2, None), staves=1, clefs=[(1, 'G', 2)])
        + _n('F', 4, 4, 'quarter', stem='up', lyric='Ho')
        + _n('G', 4, 4, 'quarter', stem='up', lyric='ly')
        + _n('A', 4, 4, 'quarter', stem='up', lyric='God')
        + _n('B', 4, 4, 'quarter', alter=-1, stem='down', lyric='is'),
        _n('A', 4, 2, 'eighth', stem='up', beam1='begin', lyric='migh')
        + _n('G', 4, 2, 'eighth', stem='up', beam1='end')
        + _n('F', 4, 4, 'quarter', stem='up', lyric='ty')
        + _n('G', 4, 8, 'half', stem='up', lyric='now'),
        _n('A', 4, 8, 'half', stem='up', lyric='A')
        + _n('G', 4, 4, 'quarter', stem='up')
        + _n('F', 4, 4, 'quarter', stem='up'),
        _n('F', 4, 16, 'whole', lyric='men'),
    ]
    cases.append({
        'id': 'chant_1staff_2_2',
        'musicxml': _wrap(m4, 'Chant 1-Staff 2/2'),
        'staves': 1,
        'voices_per_staff': [1],
        'features': ['chant_1staff', 'meter_2_2', 'keysig_flats', 'beamed_8th'],
    })

    # 5. 2-staff chant (melody + bass ison) in G major (+1 sharp), 2/4, long ties on ison
    m5 = [
        _attrs(divisions=4, fifths=1, time_sig=(2, 4, None), staves=2, clefs=[(1, 'G', 2), (2, 'F', 4)])
        + _n('G', 4, 4, 'quarter', stem='up', voice=1, staff=1)
        + _n('A', 4, 2, 'eighth', stem='up', voice=1, staff=1, beam1='begin')
        + _n('B', 4, 2, 'eighth', stem='up', voice=1, staff=1, beam1='end')
        + '<backup><duration>8</duration></backup>'
        + _n('G', 3, 8, 'half', stem='down', voice=5, staff=2, tie='start'),
        _n('C', 5, 4, 'quarter', stem='down', voice=1, staff=1)
        + _n('B', 4, 4, 'quarter', stem='down', voice=1, staff=1)
        + '<backup><duration>8</duration></backup>'
        + _n('G', 3, 8, 'half', stem='down', voice=5, staff=2, tie='both'),
        _n('A', 4, 2, 'eighth', stem='up', voice=1, staff=1, beam1='begin')
        + _n('G', 4, 2, 'eighth', stem='up', voice=1, staff=1, beam1='end')
        + _n('F', 4, 4, 'quarter', alter=1, stem='up', voice=1, staff=1)
        + '<backup><duration>8</duration></backup>'
        + _n('G', 3, 8, 'half', stem='down', voice=5, staff=2, tie='stop'),
        _n('G', 4, 8, 'half', stem='up', voice=1, staff=1)
        + '<backup><duration>8</duration></backup>'
        + _n('G', 3, 8, 'half', stem='down', voice=5, staff=2),
    ]
    cases.append({
        'id': 'chant_2staff_ison_2_4',
        'musicxml': _wrap(m5, 'Chant 2-Staff Ison 2/4'),
        'staves': 2,
        'voices_per_staff': [1, 1],
        'features': ['chant_2staff', 'meter_2_4', 'keysig_sharps', 'beamed_8th', 'ties'],
    })

    # 6. Compound 6/8 in A major (+3 sharps): 3-eighth beams, dotted quarters, dotted-8th + 16th, 8th rests
    m6 = [
        _attrs(divisions=4, fifths=3, time_sig=(6, 8, None), staves=1, clefs=[(1, 'G', 2)])
        + _n('A', 4, 2, 'eighth', stem='up', beam1='begin')
        + _n('B', 4, 2, 'eighth', stem='up', beam1='continue')
        + _n('C', 5, 2, 'eighth', alter=1, stem='up', beam1='end')
        + _n('D', 5, 6, 'quarter', dot=True, stem='down'),
        _n('E', 5, 3, 'eighth', dot=True, stem='down', beam1='begin')
        + _n('D', 5, 1, '16th', stem='down', beam1='continue', beam2='backward hook')
        + _n('C', 5, 2, 'eighth', alter=1, stem='down', beam1='end')
        + _n('B', 4, 4, 'quarter', stem='down')
        + _r(2, 'eighth'),
        _n('A', 4, 2, 'eighth', stem='up', beam1='begin')
        + _n('G', 4, 2, 'eighth', alter=1, stem='up', beam1='continue')
        + _n('F', 4, 2, 'eighth', alter=1, stem='up', beam1='end')
        + _n('E', 4, 6, 'quarter', dot=True, stem='up'),
        _n('A', 4, 6, 'quarter', dot=True, stem='up')
        + _n('A', 4, 6, 'quarter', dot=True, stem='up'),
    ]
    cases.append({
        'id': 'compound_6_8_beams',
        'musicxml': _wrap(m6, 'Compound 6/8 Beams'),
        'staves': 1,
        'voices_per_staff': [1],
        'features': ['meter_6_8', 'keysig_sharps', 'beamed_8th', 'beamed_16th', 'dots', 'rests_8th'],
    })

    # 7. All 5 rest types + dotted rests + stacked multi-voice rests + anacrusis
    m7 = [
        # Anacrusis pickup measure (quarter rest + quarter note)
        _attrs(divisions=4, fifths=0, time_sig=(4, 4, None), staves=2, clefs=[(1, 'G', 2), (2, 'F', 4)])
        + _r(4, 'quarter', voice=1, staff=1)
        + _n('G', 4, 4, 'quarter', stem='up', voice=1, staff=1)
        + '<backup><duration>8</duration></backup>'
        + _r(4, 'quarter', voice=5, staff=2)
        + _n('C', 3, 4, 'quarter', stem='down', voice=5, staff=2),
        # Whole measure rest on staff 2 while staff 1 has half rest + dotted quarter rest + eighth note
        _r(8, 'half', voice=1, staff=1)
        + _r(6, 'quarter', dot=True, voice=1, staff=1)
        + _n('A', 4, 2, 'eighth', stem='up', voice=1, staff=1)
        + '<backup><duration>16</duration></backup>'
        + _r(16, None, voice=5, staff=2, measure=True),
        # Eighth rest + 16th rest + 16th note + quarter rest + half note; stacked quarter rests on staff 2
        _r(2, 'eighth', voice=1, staff=1)
        + _r(1, '16th', voice=1, staff=1)
        + _n('B', 4, 1, '16th', stem='down', voice=1, staff=1)
        + _r(4, 'quarter', voice=1, staff=1)
        + _n('C', 5, 8, 'half', stem='down', voice=1, staff=1)
        + '<backup><duration>16</duration></backup>'
        + _r(4, 'quarter', voice=5, staff=2, display=('A', 3))
        + _n('E', 3, 4, 'quarter', stem='up', voice=5, staff=2)
        + _n('G', 3, 8, 'half', stem='up', voice=5, staff=2)
        + '<backup><duration>16</duration></backup>'
        + _r(4, 'quarter', voice=6, staff=2, display=('A', 2))
        + _n('C', 3, 4, 'quarter', stem='down', voice=6, staff=2)
        + _n('C', 3, 8, 'half', stem='down', voice=6, staff=2),
        # Final bar with whole note + half rest + half note
        _n('C', 5, 16, 'whole', voice=1, staff=1)
        + '<backup><duration>16</duration></backup>'
        + _r(8, 'half', voice=5, staff=2)
        + _n('C', 3, 8, 'half', stem='down', voice=5, staff=2),
    ]
    cases.append({
        'id': 'all_rests_anacrusis',
        'musicxml': _wrap(m7, 'All Rests and Anacrusis'),
        'staves': 2,
        'voices_per_staff': [1, 2],
        'features': ['rests_all', 'rests_whole_half', 'rests_8th', 'rests_16th', 'rests_stacked', 'anacrusis', 'dots'],
    })

    # 8. Inline accidentals (#, b, natural) + barline-tied accidentals + reversion
    m8 = [
        _attrs(divisions=4, fifths=0, time_sig=(4, 4, None), staves=1, clefs=[(1, 'G', 2)])
        + _n('F', 4, 4, 'quarter', alter=1, acc='sharp', stem='up')
        + _n('G', 4, 4, 'quarter', stem='up')
        + _n('F', 4, 4, 'quarter', alter=0, acc='natural', stem='up')
        + _n('F', 4, 4, 'quarter', alter=1, acc='sharp', stem='up', tie='start'),
        # Tied F#4 crosses barline (no new accidental printed), then untied F4 reverts to natural!
        _n('F', 4, 4, 'quarter', alter=1, stem='up', tie='stop')
        + _n('F', 4, 4, 'quarter', alter=0, stem='up')
        + _n('B', 4, 4, 'quarter', alter=-1, acc='flat', stem='down')
        + _n('B', 4, 4, 'quarter', alter=-1, stem='down', tie='start'),
        # Tied Bb4 crosses barline, then untied B4 reverts to natural, plus C#5 & E-flat
        _n('B', 4, 4, 'quarter', alter=-1, stem='down', tie='stop')
        + _n('B', 4, 4, 'quarter', alter=0, stem='down')
        + _n('C', 5, 4, 'quarter', alter=1, acc='sharp', stem='down')
        + _n('E', 5, 4, 'quarter', alter=-1, acc='flat', stem='down'),
        _n('D', 5, 8, 'half', stem='down')
        + _n('C', 5, 8, 'half', stem='down'),
    ]
    cases.append({
        'id': 'accidentals_barline_ties',
        'musicxml': _wrap(m8, 'Accidentals and Barline Ties'),
        'staves': 1,
        'voices_per_staff': [1],
        'features': ['accidentals', 'tied_barline_accidental', 'ties', 'meter_4_4'],
    })

    # 9. High and low ledger lines (treble A3..E6, bass C2..E4) across filled, hollow, whole
    m9 = [
        _attrs(divisions=4, fifths=0, time_sig=(4, 4, None), staves=2, clefs=[(1, 'G', 2), (2, 'F', 4)])
        + _n('C', 4, 4, 'quarter', stem='up', voice=1, staff=1)
        + _n('B', 3, 4, 'quarter', stem='up', voice=1, staff=1)
        + _n('A', 3, 8, 'half', stem='up', voice=1, staff=1)
        + '<backup><duration>16</duration></backup>'
        + _n('E', 2, 4, 'quarter', stem='up', voice=5, staff=2)
        + _n('D', 2, 4, 'quarter', stem='up', voice=5, staff=2)
        + _n('C', 2, 8, 'half', stem='up', voice=5, staff=2),
        _n('A', 5, 4, 'quarter', stem='down', voice=1, staff=1)
        + _n('B', 5, 4, 'quarter', stem='down', voice=1, staff=1)
        + _n('C', 6, 4, 'quarter', stem='down', voice=1, staff=1)
        + _n('D', 6, 4, 'quarter', stem='down', voice=1, staff=1)
        + '<backup><duration>16</duration></backup>'
        + _n('C', 4, 4, 'quarter', stem='down', voice=5, staff=2)
        + _n('D', 4, 4, 'quarter', stem='down', voice=5, staff=2)
        + _n('E', 4, 8, 'half', stem='down', voice=5, staff=2),
        _n('E', 6, 16, 'whole', voice=1, staff=1)
        + '<backup><duration>16</duration></backup>'
        + _n('C', 2, 16, 'whole', voice=5, staff=2),
    ]
    cases.append({
        'id': 'ledger_lines_extremes',
        'musicxml': _wrap(m9, 'Ledger Lines Extremes'),
        'staves': 2,
        'voices_per_staff': [1, 1],
        'features': ['ledger_lines', 'meter_4_4'],
    })

    # 10. Beamed 16ths, flagged 16ths, dotted-8th+16th, and eighth-note triplets (divisions=12)
    m10 = [
        _attrs(divisions=12, fifths=0, time_sig=(4, 4, None), staves=1, clefs=[(1, 'G', 2)])
        # 4 beamed 16ths (3 ticks each = 12) + dotted 8th (9) + 16th (3) + quarter (12) + quarter (12)
        + _n('C', 5, 3, '16th', stem='down', beam1='begin', beam2='begin')
        + _n('D', 5, 3, '16th', stem='down', beam1='continue', beam2='continue')
        + _n('E', 5, 3, '16th', stem='down', beam1='continue', beam2='continue')
        + _n('D', 5, 3, '16th', stem='down', beam1='end', beam2='end')
        + _n('C', 5, 9, 'eighth', dot=True, stem='down', beam1='begin')
        + _n('B', 4, 3, '16th', stem='down', beam1='end', beam2='backward hook')
        + _n('A', 4, 12, 'quarter', stem='up')
        + _n('G', 4, 12, 'quarter', stem='up'),
        # Eighth-note triplet (4 ticks each = 12) + quarter + eighth-note triplet + quarter
        _n('G', 4, 4, 'eighth', stem='up', beam1='begin', time_mod=(3, 2), tuplet='start')
        + _n('A', 4, 4, 'eighth', stem='up', beam1='continue', time_mod=(3, 2))
        + _n('B', 4, 4, 'eighth', stem='up', beam1='end', time_mod=(3, 2), tuplet='stop')
        + _n('C', 5, 12, 'quarter', stem='down')
        + _n('D', 5, 4, 'eighth', stem='down', beam1='begin', time_mod=(3, 2), tuplet='start')
        + _n('C', 5, 4, 'eighth', stem='down', beam1='continue', time_mod=(3, 2))
        + _n('B', 4, 4, 'eighth', stem='down', beam1='end', time_mod=(3, 2), tuplet='stop')
        + _n('A', 4, 12, 'quarter', stem='up'),
        # Flagged 16th + 16th rest + flagged 8th + half note + quarter note
        _n('G', 4, 3, '16th', stem='up')
        + _r(3, '16th')
        + _n('A', 4, 6, 'eighth', stem='up')
        + _n('B', 4, 24, 'half', stem='down')
        + _n('C', 5, 12, 'quarter', stem='down'),
    ]
    cases.append({
        'id': 'sixteenths_and_triplets',
        'musicxml': _wrap(m10, 'Sixteenths and Triplets'),
        'staves': 1,
        'voices_per_staff': [1],
        'features': ['beamed_16th', 'triplets', 'dots', 'rests_16th'],
    })

    # 11. Divisi 2nd-apart & 3rd-apart touching chords (hollow and filled) in C common time
    m11 = [
        _satb_bar(
            [_n('G', 4, 4, 'quarter', stem='up', voice=1, staff=1),
             _n('A', 4, 4, 'quarter', stem='up', voice=1, staff=1),
             _n('B', 4, 8, 'half', stem='up', voice=1, staff=1)],
            [_n('F', 4, 4, 'quarter', stem='down', voice=2, staff=1),   # 2nd apart!
             _n('F', 4, 4, 'quarter', stem='down', voice=2, staff=1),   # 3rd apart!
             _n('A', 4, 8, 'half', stem='down', voice=2, staff=1)],     # hollow 2nd apart!
            [_n('D', 4, 4, 'quarter', stem='up', voice=5, staff=2),
             _n('C', 4, 4, 'quarter', stem='up', voice=5, staff=2),
             _n('D', 4, 8, 'half', stem='up', voice=5, staff=2)],
            [_n('C', 4, 4, 'quarter', stem='down', voice=6, staff=2),   # 2nd apart!
             _n('A', 3, 4, 'quarter', stem='down', voice=6, staff=2),   # 3rd apart!
             _n('B', 3, 8, 'half', stem='down', voice=6, staff=2)],     # hollow 3rd apart!
            16,
            prefix=_attrs(divisions=4, fifths=0, time_sig=(4, 4, 'common'), staves=2, clefs=[(1, 'G', 2), (2, 'F', 4)]),
        ),
        _satb_bar(
            # Single-stem chord clusters with 2nds and 3rds
            [_n('C', 5, 4, 'quarter', stem='up', voice=1, staff=1),
             _n('B', 4, 4, 'quarter', stem='up', voice=1, staff=1, chord=True),
             _n('D', 5, 4, 'quarter', stem='up', voice=1, staff=1),
             _n('B', 4, 4, 'quarter', stem='up', voice=1, staff=1, chord=True),
             _n('C', 5, 8, 'half', stem='up', voice=1, staff=1),
             _n('A', 4, 8, 'half', stem='up', voice=1, staff=1, chord=True)],
            [_n('G', 4, 8, 'half', stem='down', voice=2, staff=1),
             _n('F', 4, 8, 'half', stem='down', voice=2, staff=1)],
            [_n('E', 4, 4, 'quarter', stem='up', voice=5, staff=2),
             _n('D', 4, 4, 'quarter', stem='up', voice=5, staff=2, chord=True),
             _n('F', 4, 4, 'quarter', stem='up', voice=5, staff=2),
             _n('D', 4, 4, 'quarter', stem='up', voice=5, staff=2, chord=True),
             _n('E', 4, 8, 'half', stem='up', voice=5, staff=2)],
            [_n('C', 3, 8, 'half', stem='down', voice=6, staff=2),
             _n('C', 3, 8, 'half', stem='down', voice=6, staff=2)],
            16,
        ),
        _satb_bar(
            [_n('C', 5, 16, 'whole', voice=1, staff=1)],
            [_n('G', 4, 16, 'whole', voice=2, staff=1)],
            [_n('E', 4, 16, 'whole', voice=5, staff=2)],
            [_n('C', 3, 16, 'whole', voice=6, staff=2)],
            16,
        ),
    ]
    cases.append({
        'id': 'divisi_chords_seconds_thirds',
        'musicxml': _wrap(m11, 'Divisi 2nd and 3rd Chords'),
        'staves': 2,
        'voices_per_staff': [2, 2],
        'features': ['divisi_2nd_3rd', 'satb', 'meter_common'],
    })

    # 12. 2-staff TTBB men's choir with printed Tenor G8vb (clef-octave-change=-1) + Bass F4, G major (+1 sharp), 4/4, 8 bars (2 systems).
    # Uses 2 staves (not 3) so ScoreReader's 3-staff choir shortcut cannot mask missed printed-8 detection.
    m12 = [
        _satb_bar(
            [_n('B', 3, 4, 'quarter', stem='up', voice=1, staff=1),
             _n('C', 4, 4, 'quarter', stem='up', voice=1, staff=1),
             _n('D', 4, 4, 'quarter', stem='up', voice=1, staff=1),
             _n('E', 4, 4, 'quarter', stem='up', voice=1, staff=1)],
            [_n('G', 3, 4, 'quarter', stem='down', voice=2, staff=1),
             _n('A', 3, 4, 'quarter', stem='down', voice=2, staff=1),
             _n('B', 3, 4, 'quarter', stem='down', voice=2, staff=1),
             _n('C', 4, 4, 'quarter', stem='down', voice=2, staff=1)],
            [_n('D', 3, 4, 'quarter', stem='up', voice=5, staff=2),
             _n('E', 3, 4, 'quarter', stem='up', voice=5, staff=2),
             _n('D', 3, 4, 'quarter', stem='up', voice=5, staff=2),
             _n('C', 3, 4, 'quarter', stem='up', voice=5, staff=2)],
            [_n('G', 2, 4, 'quarter', stem='down', voice=6, staff=2),
             _n('A', 2, 4, 'quarter', stem='down', voice=6, staff=2),
             _n('B', 2, 4, 'quarter', stem='down', voice=6, staff=2),
             _n('C', 3, 4, 'quarter', stem='down', voice=6, staff=2)],
            16,
            prefix=_attrs(
                divisions=4,
                fifths=1,
                time_sig=(4, 4, None),
                staves=2,
                clefs=[(1, 'G', 2, -1), (2, 'F', 4)],
            ),
        ),
        _satb_bar(
            [_n('D', 4, 4, 'quarter', stem='up', voice=1, staff=1),
             _n('C', 4, 2, 'eighth', stem='up', voice=1, staff=1, beam1='begin'),
             _n('B', 3, 2, 'eighth', stem='up', voice=1, staff=1, beam1='end'),
             _n('A', 3, 4, 'quarter', stem='up', voice=1, staff=1),
             _n('B', 3, 4, 'quarter', stem='up', voice=1, staff=1)],
            [_n('B', 3, 4, 'quarter', stem='down', voice=2, staff=1),
             _n('A', 3, 4, 'quarter', stem='down', voice=2, staff=1),
             _n('F', 3, 4, 'quarter', alter=1, stem='down', voice=2, staff=1),
             _n('G', 3, 4, 'quarter', stem='down', voice=2, staff=1)],
            [_n('D', 3, 4, 'quarter', stem='up', voice=5, staff=2),
             _n('E', 3, 4, 'quarter', stem='up', voice=5, staff=2),
             _n('D', 3, 4, 'quarter', stem='up', voice=5, staff=2),
             _n('D', 3, 4, 'quarter', stem='up', voice=5, staff=2)],
            [_n('G', 2, 4, 'quarter', stem='down', voice=6, staff=2),
             _n('C', 3, 4, 'quarter', stem='down', voice=6, staff=2),
             _n('D', 3, 4, 'quarter', stem='down', voice=6, staff=2),
             _n('G', 2, 4, 'quarter', stem='down', voice=6, staff=2)],
            16,
        ),
        _satb_bar(
            [_n('C', 4, 4, 'quarter', stem='up', voice=1, staff=1),
             _n('B', 3, 4, 'quarter', stem='up', voice=1, staff=1),
             _n('A', 3, 4, 'quarter', stem='up', voice=1, staff=1),
             _r(4, 'quarter', voice=1, staff=1, display=('E', 4))],
            [_n('G', 3, 4, 'quarter', stem='down', voice=2, staff=1),
             _n('G', 3, 4, 'quarter', stem='down', voice=2, staff=1),
             _n('F', 3, 4, 'quarter', alter=1, stem='down', voice=2, staff=1),
             _r(4, 'quarter', voice=2, staff=1, display=('E', 3))],
            [_n('E', 3, 4, 'quarter', stem='up', voice=5, staff=2),
             _n('D', 3, 4, 'quarter', stem='up', voice=5, staff=2),
             _n('D', 3, 4, 'quarter', stem='up', voice=5, staff=2),
             _r(4, 'quarter', voice=5, staff=2, display=('A', 3))],
            [_n('C', 3, 4, 'quarter', stem='down', voice=6, staff=2),
             _n('G', 2, 4, 'quarter', stem='down', voice=6, staff=2),
             _n('D', 2, 4, 'quarter', stem='down', voice=6, staff=2),
             _r(4, 'quarter', voice=6, staff=2, display=('A', 2))],
            16,
        ),
        _satb_bar(
            [_n('B', 3, 4, 'quarter', stem='up', voice=1, staff=1),
             _n('C', 4, 4, 'quarter', stem='up', voice=1, staff=1),
             _n('D', 4, 4, 'quarter', stem='up', voice=1, staff=1),
             _n('C', 4, 4, 'quarter', stem='up', voice=1, staff=1)],
            [_n('G', 3, 4, 'quarter', stem='down', voice=2, staff=1),
             _n('A', 3, 4, 'quarter', stem='down', voice=2, staff=1),
             _n('B', 3, 4, 'quarter', stem='down', voice=2, staff=1),
             _n('A', 3, 4, 'quarter', stem='down', voice=2, staff=1)],
            [_n('D', 3, 4, 'quarter', stem='up', voice=5, staff=2),
             _n('E', 3, 4, 'quarter', stem='up', voice=5, staff=2),
             _n('D', 3, 4, 'quarter', stem='up', voice=5, staff=2),
             _n('E', 3, 4, 'quarter', stem='up', voice=5, staff=2)],
            [_n('G', 2, 4, 'quarter', stem='down', voice=6, staff=2),
             _n('A', 2, 4, 'quarter', stem='down', voice=6, staff=2),
             _n('B', 2, 4, 'quarter', stem='down', voice=6, staff=2),
             _n('A', 2, 4, 'quarter', stem='down', voice=6, staff=2)],
            16,
        ),
        _satb_bar(
            [_n('D', 4, 4, 'quarter', stem='up', voice=1, staff=1),
             _n('E', 4, 4, 'quarter', stem='up', voice=1, staff=1),
             _n('D', 4, 4, 'quarter', stem='up', voice=1, staff=1),
             _n('C', 4, 4, 'quarter', stem='up', voice=1, staff=1)],
            [_n('B', 3, 4, 'quarter', stem='down', voice=2, staff=1),
             _n('C', 4, 4, 'quarter', stem='down', voice=2, staff=1),
             _n('B', 3, 4, 'quarter', stem='down', voice=2, staff=1),
             _n('A', 3, 4, 'quarter', stem='down', voice=2, staff=1)],
            [_n('D', 3, 4, 'quarter', stem='up', voice=5, staff=2),
             _n('C', 3, 4, 'quarter', stem='up', voice=5, staff=2),
             _n('D', 3, 4, 'quarter', stem='up', voice=5, staff=2),
             _n('E', 3, 4, 'quarter', stem='up', voice=5, staff=2)],
            [_n('G', 2, 4, 'quarter', stem='down', voice=6, staff=2),
             _n('C', 3, 4, 'quarter', stem='down', voice=6, staff=2),
             _n('B', 2, 4, 'quarter', stem='down', voice=6, staff=2),
             _n('A', 2, 4, 'quarter', stem='down', voice=6, staff=2)],
            16,
        ),
        _satb_bar(
            [_n('B', 3, 2, 'eighth', stem='up', voice=1, staff=1, beam1='begin'),
             _n('C', 4, 2, 'eighth', stem='up', voice=1, staff=1, beam1='end'),
             _n('D', 4, 4, 'quarter', stem='up', voice=1, staff=1),
             _n('C', 4, 4, 'quarter', stem='up', voice=1, staff=1),
             _n('B', 3, 4, 'quarter', stem='up', voice=1, staff=1)],
            [_n('G', 3, 4, 'quarter', stem='down', voice=2, staff=1),
             _n('B', 3, 4, 'quarter', stem='down', voice=2, staff=1),
             _n('A', 3, 4, 'quarter', stem='down', voice=2, staff=1),
             _n('G', 3, 4, 'quarter', stem='down', voice=2, staff=1)],
            [_n('D', 3, 4, 'quarter', stem='up', voice=5, staff=2),
             _n('D', 3, 4, 'quarter', stem='up', voice=5, staff=2),
             _n('E', 3, 4, 'quarter', stem='up', voice=5, staff=2),
             _n('D', 3, 4, 'quarter', stem='up', voice=5, staff=2)],
            [_n('G', 2, 4, 'quarter', stem='down', voice=6, staff=2),
             _n('G', 2, 4, 'quarter', stem='down', voice=6, staff=2),
             _n('C', 3, 4, 'quarter', stem='down', voice=6, staff=2),
             _n('G', 2, 4, 'quarter', stem='down', voice=6, staff=2)],
            16,
        ),
        _satb_bar(
            [_n('B', 3, 8, 'half', stem='up', voice=1, staff=1),
             _n('A', 3, 8, 'half', stem='up', voice=1, staff=1)],
            [_n('G', 3, 8, 'half', stem='down', voice=2, staff=1),
             _n('F', 3, 8, 'half', alter=1, stem='down', voice=2, staff=1)],
            [_n('D', 3, 8, 'half', stem='up', voice=5, staff=2),
             _n('D', 3, 8, 'half', stem='up', voice=5, staff=2)],
            [_n('D', 3, 8, 'half', stem='down', voice=6, staff=2),
             _n('D', 2, 8, 'half', stem='down', voice=6, staff=2)],
            16,
        ),
        _satb_bar(
            [_n('G', 3, 16, 'whole', voice=1, staff=1)],
            [_n('D', 3, 16, 'whole', voice=2, staff=1)],
            [_n('B', 2, 16, 'whole', voice=5, staff=2)],
            [_n('G', 2, 16, 'whole', voice=6, staff=2)],
            16,
        ),
    ]
    cases.append({
        'id': 'satb_tenor_g8vb',
        'musicxml': _wrap(m12, 'TTBB Tenor G8vb'),
        'staves': 2,
        'voices_per_staff': [2, 2],
        'features': ['satb', 'clef_g8vb', 'keysig_sharps', 'meter_4_4', 'beamed_8th'],
    })

    return cases


# ---------------------------------------------------------------------------
# Rendering, scan degradation, ScoreReader execution, and eval_f1 scoring
# ---------------------------------------------------------------------------

def render_musicxml_to_png(musicxml_text: str, font_name: str, out_png: Path, width_px: int = 2480) -> Path:
    """Renders MusicXML with Verovio using a SMuFL font and rasterizes at 300 DPI via rsvg-convert."""
    verovio.enableLog(verovio.LOG_OFF)
    tk = verovio.toolkit()
    tk.setOptions({
        'font': font_name,
        'scale': 42,
        'pageWidth': 2100,
        'pageHeight': 2970,
        'adjustPageHeight': True,
        'footer': 'none',
        'header': 'none',
        'svgViewBox': True,
    })
    tk.loadData(musicxml_text)
    svg = tk.renderToSVG(1)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [RSVG_CONVERT, '-b', 'white', '-w', str(width_px), '-o', str(out_png)],
        input=svg.encode('utf-8'),
        stderr=subprocess.PIPE,
        check=True,
    )
    _ = proc
    return out_png


def degrade_mild_scan(grey: np.ndarray, seed: int) -> np.ndarray:
    """Applies mild scan blur, toner pinholes inside ink, contrast compression, and light noise."""
    rng = np.random.default_rng(seed)
    out = grey.astype(np.float32)
    dark_mask = out < 120.0
    ys, xs = np.nonzero(dark_mask)
    if len(ys) > 50:
        n_holes = min(len(ys) // 55, 650)
        pick = rng.choice(len(ys), size=max(1, n_holes), replace=False)
        for idx in pick:
            cv2.circle(out, (int(xs[idx]), int(ys[idx])), 1, float(rng.uniform(165.0, 235.0)), -1)
    out = cv2.GaussianBlur(out, (0, 0), 0.65)
    out = 18.0 + (out / 255.0) * (246.0 - 18.0)
    out = out + rng.normal(0.0, 3.2, out.shape)
    return np.clip(out, 0.0, 255.0).astype(np.uint8)


def run_scorereader_on_png(png_path: Path, title: str = 'roundtrip') -> tuple[str | None, float]:
    """Runs ScoreReader end-to-end on one PNG image and returns (musicxml_text, elapsed_sec)."""
    t0 = time.time()
    grey = cv2.imread(str(png_path), cv2.IMREAD_GRAYSCALE)
    if grey is None:
        return None, time.time() - t0
    grey = flat_paper(grey)
    staves = find_staves(grey)
    if not staves:
        return None, time.time() - t0
    systems = find_systems(grey, staves)
    staves, systems = lost_staves(grey, staves, systems)
    clean, places = clean_page(grey, staves, systems)
    res = read_page(clean, places, title=title)
    return res['musicxml'], time.time() - t0


def score_musicxml_pair(gt_xml_path: Path, pred_xml_path: Path, voices_per_staff: list[int]) -> dict[str, Any]:
    """Evaluates predicted MusicXML against exact ground-truth MusicXML using bench/eval_f1.py helpers."""
    gt = read_musicxml(gt_xml_path)
    gt_notes_joined = [join_ties(s) for s in gt['notes']]
    gt_tokens = [reader_tokens(s) for s in gt_notes_joined]

    if not pred_xml_path.exists():
        pred = {'notes': [], 'rests': [], 'meters': []}
    else:
        try:
            pred = read_musicxml(pred_xml_path)
        except Exception:
            pred = {'notes': [], 'rests': [], 'meters': []}

    pred_notes_joined = [join_ties(s) for s in pred['notes']]
    pred_staves = split_by_clef(pred_notes_joined, len(gt_tokens))
    pred_tokens = [reader_tokens(s) for s in pred_staves]
    chosen = match_staves(gt_tokens, pred_tokens)

    staff_sum = Counter()
    part_sum = Counter()
    len_conf = Counter()
    pitch_err = Counter()
    rest_matched = rest_exp = rest_act = 0

    for row, exp_tok in enumerate(gt_tokens):
        idx = chosen[row]
        rd = pred_tokens[idx] if idx is not None else []
        _, pairs = align_notes(exp_tok, rd)
        sc = tally_pairs(exp_tok, rd, pairs)
        for k, v in sc.items():
            if isinstance(v, int):
                staff_sum[k] += v
        len_conf.update(sc['len_conf'])
        pitch_err.update(sc['pitch_err'])

        # Rest scoring on this staff
        exp_r_raw = gt['rests'][row] if row < len(gt['rests']) else []
        act_r_raw = pred['rests'][idx] if (idx is not None and idx < len(pred['rests'])) else []
        exp_r = sorted({(r['on'], r['len']) for r in exp_r_raw if r['len'] > 0})
        act_r = sorted({(r['on'], r['len']) for r in act_r_raw if r['len'] > 0})
        rm, re_n, ra_n = align_rests(exp_r, act_r)
        rest_matched += rm
        rest_exp += re_n
        rest_act += ra_n

        # Part-level scoring (split 2-voice SATB staves cleanly)
        n_v = voices_per_staff[row] if row < len(voices_per_staff) else 1
        if n_v <= 1:
            for k, v in sc.items():
                if isinstance(v, int):
                    part_sum[k] += v
        else:
            exp_up, exp_lo = split_parts(exp_tok, exp_r_raw)
            act_up, act_lo = split_parts(rd, act_r_raw)
            for pe, pa in ((exp_up, act_up), (exp_lo, act_lo)):
                _, ppairs = align_notes(pe, pa)
                psc = tally_pairs(pe, pa, ppairs)
                for k, v in psc.items():
                    if isinstance(v, int):
                        part_sum[k] += v

    # Opening meter and full unique meter sequence check
    gt_meters = [norm_meter(m) for m in gt['meters'] if norm_meter(m)]
    pred_meters = [norm_meter(m) for m in pred['meters'] if norm_meter(m)]
    exp_m0 = gt_meters[0] if gt_meters else None
    act_m0 = pred_meters[0] if pred_meters else None
    meter_ok = (act_m0 == exp_m0) if exp_m0 is not None else None
    gt_uniq = list(dict.fromkeys(gt_meters))
    pred_uniq = list(dict.fromkeys(pred_meters))
    mid_meters_ok = all(m in pred_uniq for m in gt_uniq) if len(gt_uniq) > 1 else None

    _, _, sf1 = prf(staff_sum['right'], staff_sum['expected'], staff_sum['read'])
    _, _, pf1 = prf(part_sum['right'], part_sum['expected'], part_sum['read'])
    _, _, rf1 = prf(rest_matched, rest_exp, rest_act)
    onset_ex = staff_sum['onset_exact'] / max(1, staff_sum['right'])

    return {
        'staff': dict(staff_sum),
        'parts': dict(part_sum),
        'staff_f1': sf1,
        'parts_f1': pf1,
        'rests': {'matched': rest_matched, 'expected': rest_exp, 'actual': rest_act, 'f1': rf1},
        'onset_exact': onset_ex,
        'meter_expected': exp_m0,
        'meter_actual': act_m0,
        'meter_ok': meter_ok,
        'gt_meters': gt_uniq,
        'pred_meters': pred_uniq,
        'mid_meters_ok': mid_meters_ok,
        'len_conf': dict(len_conf),
        'pitch_err': dict(pitch_err),
    }


def _eval_one_job(task: tuple[dict[str, Any], str, str, str, int]) -> dict[str, Any]:
    """Worker: renders one (case, font, condition), runs ScoreReader, and returns scored metrics."""
    case, font_name, condition, work_dir_s, seed = task
    work_dir = Path(work_dir_s)
    cid = case['id']
    tag = f'{cid}__{font_name}__{condition}'
    gt_path = work_dir / f'{cid}.gt.musicxml'
    if not gt_path.exists():
        gt_path.parent.mkdir(parents=True, exist_ok=True)
        gt_path.write_text(case['musicxml'], encoding='utf-8')

    clean_png = work_dir / f'{cid}__{font_name}__clean.png'
    if not clean_png.exists():
        render_musicxml_to_png(case['musicxml'], font_name, clean_png)

    if condition == 'degraded':
        png_path = work_dir / f'{tag}.png'
        raw = cv2.imread(str(clean_png), cv2.IMREAD_GRAYSCALE)
        deg = degrade_mild_scan(raw, seed)
        cv2.imwrite(str(png_path), deg)
    else:
        png_path = clean_png

    pred_xml_path = work_dir / f'{tag}.pred.musicxml'
    xml_text, sec = run_scorereader_on_png(png_path, title=tag)
    if xml_text:
        pred_xml_path.write_text(xml_text, encoding='utf-8')

    scored = score_musicxml_pair(gt_path, pred_xml_path, case['voices_per_staff'])
    scored.update({
        'id': cid,
        'font': font_name,
        'condition': condition,
        'features': case['features'],
        'seconds': round(sec, 2),
        'png': str(png_path),
        'gt_xml': str(gt_path),
    })
    return scored


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    s_tot, p_tot, r_tot, lc, pe = Counter(), Counter(), Counter(), Counter(), Counter()
    m_ok = m_tot = 0
    for r in rows:
        s_tot.update(r['staff'])
        p_tot.update(r['parts'])
        r_tot.update({k: v for k, v in r['rests'].items() if isinstance(v, int)})
        lc.update(r['len_conf'])
        pe.update(r['pitch_err'])
        if r['meter_ok'] is not None:
            m_tot += 1
            m_ok += int(r['meter_ok'])
    sp, sr, sf1 = prf(s_tot['right'], s_tot['expected'], s_tot['read'])
    pp, pr, pf1 = prf(p_tot['right'], p_tot['expected'], p_tot['read'])
    rp, rr, rf1 = prf(r_tot['matched'], r_tot['expected'], r_tot['actual'])
    onset = s_tot['onset_exact'] / max(1, s_tot['right'])
    dt = s_tot['dt_ok'] / max(1, s_tot['dt_total'])
    return {
        'runs': len(rows),
        'staff_f1': sf1, 'staff_prec': sp, 'staff_rec': sr, 'staff': dict(s_tot),
        'parts_f1': pf1, 'parts_prec': pp, 'parts_rec': pr, 'parts': dict(p_tot),
        'rest_f1': rf1, 'rest_prec': rp, 'rest_rec': rr, 'rests': dict(r_tot),
        'onset_exact': onset, 'onset_dt': dt,
        'meter_ok': m_ok, 'meter_total': m_tot,
        'len_conf': dict(lc.most_common(10)),
        'pitch_err': dict(pe),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Multi-font Verovio round-trip benchmark for ScoreReader.')
    parser.add_argument('--fonts', default=','.join(SMUFL_FONTS), help='Comma-separated SMuFL fonts')
    parser.add_argument('--conditions', default='clean,degraded', help='Comma-separated conditions: clean,degraded')
    parser.add_argument('--cases', default=None, help='Optional comma-separated subset of case IDs')
    parser.add_argument('--out-dir', default=str(TMP_OUT), help='Temporary directory for PNGs and XMLs')
    parser.add_argument('--json-out', default=str(TMP_OUT / 'roundtrip_summary.json'), help='JSON summary output path')
    parser.add_argument('--workers', type=int, default=8, help='Parallel worker processes')
    args = parser.parse_args()

    os.environ.setdefault('OMP_NUM_THREADS', '1')
    os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')

    fonts = [f.strip() for f in args.fonts.split(',') if f.strip()]
    conditions = [c.strip() for c in args.conditions.split(',') if c.strip()]
    suite = build_roundtrip_suite()
    if args.cases:
        keep = {c.strip() for c in args.cases.split(',') if c.strip()}
        suite = [c for c in suite if c['id'] in keep]

    work_dir = Path(args.out_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    # Pre-render all clean PNGs first so clean + degraded tasks never race on the same PNG path.
    t0 = time.time()
    for case in suite:
        (work_dir / f"{case['id']}.gt.musicxml").write_text(case['musicxml'], encoding='utf-8')
        for font in fonts:
            c_png = work_dir / f"{case['id']}__{font}__clean.png"
            render_musicxml_to_png(case['musicxml'], font, c_png)

    tasks = []
    idx = 0
    for case in suite:
        for font in fonts:
            for cond in conditions:
                tasks.append((case, font, cond, str(work_dir), 7000 + idx * 31))
                idx += 1

    rows: list[dict[str, Any]] = []
    if args.workers > 1:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            rows = list(pool.map(_eval_one_job, tasks))
    else:
        rows = [_eval_one_job(t) for t in tasks]

    elapsed = time.time() - t0
    overall = _aggregate(rows)

    print(f'=== VEROVIO ROUND-TRIP BENCHMARK ({len(suite)} scores x {len(fonts)} fonts x {len(conditions)} conds = {len(rows)} runs in {elapsed:.1f}s) ===')
    print(f"Overall Staff F1={overall['staff_f1']:6.2%} (P={overall['staff_prec']:6.2%} R={overall['staff_rec']:6.2%}) | "
          f"Parts F1={overall['parts_f1']:6.2%} | Rest F1={overall['rest_f1']:6.2%} ({overall['rests'].get('matched',0)}/{overall['rests'].get('expected',0)}, em={overall['rests'].get('actual',0)}) | "
          f"Onset={overall['onset_exact']:6.2%} | Meter={overall['meter_ok']}/{overall['meter_total']}")

    print('\n--- By Condition ---')
    by_cond = {}
    for cond in conditions:
        agg = _aggregate([r for r in rows if r['condition'] == cond])
        by_cond[cond] = agg
        print(f"  {cond:10s}: Staff F1={agg['staff_f1']:6.2%} | Parts F1={agg['parts_f1']:6.2%} | "
              f"Rest F1={agg['rest_f1']:6.2%} | Onset={agg['onset_exact']:6.2%} | Meter={agg['meter_ok']}/{agg['meter_total']}")

    print('\n--- By SMuFL Font ---')
    by_font = {}
    for font in fonts:
        agg = _aggregate([r for r in rows if r['font'] == font])
        by_font[font] = agg
        print(f"  {font:10s}: Staff F1={agg['staff_f1']:6.2%} (P={agg['staff_prec']:6.2%} R={agg['staff_rec']:6.2%}) | "
              f"Rest F1={agg['rest_f1']:6.2%} | Onset={agg['onset_exact']:6.2%} | Meter={agg['meter_ok']}/{agg['meter_total']}")

    print('\n--- By Score Case (all fonts & conditions) ---')
    by_case = {}
    for case in suite:
        cid = case['id']
        agg = _aggregate([r for r in rows if r['id'] == cid])
        by_case[cid] = agg
        st = agg['staff']
        print(f"  {cid:30s}: Staff F1={agg['staff_f1']:6.2%} Parts F1={agg['parts_f1']:6.2%} | "
              f"Rest F1={agg['rest_f1']:6.2%} | Onset={agg['onset_exact']:6.2%} | Meter={agg['meter_ok']}/{agg['meter_total']} | "
              f"miss={st.get('missed',0):3d} ext={st.get('extra',0):3d} p={st.get('pitch_only',0):2d} l={st.get('len_only',0):3d}")

    print('\n--- By Feature Tag ---')
    feat_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        for f in r['features']:
            feat_map[f].append(r)
    by_feat = {}
    for feat in sorted(feat_map):
        agg = _aggregate(feat_map[feat])
        by_feat[feat] = agg
        print(f"  {feat:24s}: Staff F1={agg['staff_f1']:6.2%} | Rest F1={agg['rest_f1']:6.2%} | "
              f"Onset={agg['onset_exact']:6.2%} | Meter={agg['meter_ok']}/{agg['meter_total']} | top_len={list(agg['len_conf'].items())[:3]}")

    print(f"\nTop length confusions: {overall['len_conf']}")
    print(f"Pitch error breakdown: {overall['pitch_err']}")

    if args.json_out:
        out_p = Path(args.json_out)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps({
            'overall': overall,
            'by_condition': by_cond,
            'by_font': by_font,
            'by_case': by_case,
            'by_feature': by_feat,
            'runs': rows,
        }, indent=2) + '\n', encoding='utf-8')
        print(f'Wrote JSON summary -> {out_p}')
    return 0


if __name__ == '__main__':
    sys.exit(main())

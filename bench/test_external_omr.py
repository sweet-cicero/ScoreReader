#!/usr/bin/env python3
"""Offline unit and smoke integration tests for external OMR harnesses.

Tests (100% offline, zero cloud calls, zero holdout access):
  1. Verovio offline SVG rendering across all 5 SMuFL fonts + **kern and ABC conversion.
  2. LEGATO LegatoModel import + offline load readiness + abc2xml.py & Verovio ABC->MusicXML
     conversion + live bfloat16 inference when cached (or clean gated-checkpoint skip).
  3. **kern -> MusicXML normalization and conversion (music21 + resilient fallback).
  4. ScoreReader systems.py cropping + live offline SMT++ full-page (PRAIG/smt-fp-grandstaff)
     AND system-cropped (antoniorv6/smt-grandstaff with legacy decoder remapping & end-ReLU,
     asserting 0 missing keys).
  5. Live offline ScoreReader and oemer ONNX inference (with ORT_ENABLE_EXTENDED shim).

Usage:
  PYTHONDONTWRITEBYTECODE=1 out/tools/omr-bench/verovio-venv/bin/python bench/test_external_omr.py
"""
from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bench.eval_f1 import read_musicxml
from bench.external_omr import (
    check_legato_offline,
    check_verovio_offline,
    crop_systems_with_scorereader,
    ensure_rgb_png,
    kern_to_musicxml,
    run_legato_batch,
    run_oemer_on_png,
    run_smt_batch,
)
from bench.test_verovio_roundtrip import build_roundtrip_suite, render_musicxml_to_png, run_scorereader_on_png

TMP = Path('/tmp/scorereader_swarm/omr_eval/test_external_omr')


def _ensure_smoke_satb_png() -> Path:
    suite = {c['id']: c for c in build_roundtrip_suite()}
    xml = suite['satb_hymn_4_4_sharps']['musicxml']
    png = TMP / 'smoke_satb.png'
    if not png.exists():
        render_musicxml_to_png(xml, 'Bravura', png, width_px=2200)
        ensure_rgb_png(png, png)
    return png


def test_verovio_offline() -> None:
    """Verifies Verovio SVG rendering across all 5 SMuFL fonts plus **kern and ABC conversion."""
    info = check_verovio_offline(TMP / 'verovio')
    assert info['kern_svg_ok'], f'Verovio failed on one or more SMuFL fonts: {info}'
    assert info['abc_svg_ok'], f'Verovio failed to parse ABC: {info}'
    assert info['kern_to_musicxml_ok'], f'kern_to_musicxml failed: {info}'
    print(f"    verovio {info['version']} fonts=5/5 kern_conv={info['kern_converter']}")


def test_legato_offline() -> None:
    """Verifies LEGATO import, ABC->MusicXML conversion, and live offline inference if cached."""
    info = check_legato_offline(TMP / 'legato')
    assert info['import_ok'], f'LegatoModel import failed: {info}'
    assert info['abc2xml_ok'], f'LEGATO abc2xml.py conversion failed: {info}'
    assert info['verovio_abc_ok'], f'Verovio ABC verification failed: {info}'
    if info['live_ready']:
        png = _ensure_smoke_satb_png()
        job = [{
            'id': 'smoke_satb',
            'image': str(png),
            'abc_out': str(TMP / 'legato' / 'smoke_satb.abc'),
            'xml_out': str(TMP / 'legato' / 'smoke_satb.musicxml'),
        }]
        res = run_legato_batch(job, TMP / 'legato', max_new_tokens=200, num_beams=1, threads=12)
        assert res['status'] == 'live_ok', f'LEGATO live inference failed: {res}'
        r0 = res['results'][0]
        assert r0['tokens'] >= 30 and r0['xml_ok'], f'LEGATO produced invalid output: {r0}'
        n_notes = sum(len(s) for s in read_musicxml(Path(r0['xml_out']))['notes'])
        print(f"    legato LIVE params={res['params']:,} sec={r0['seconds']} toks={r0['tokens']} xml_notes={n_notes}")
    else:
        print(f"    legato import=OK abc2xml_notes={info['abc2xml_notes']} status={info['status']}")


def test_kern_converter_resilience() -> None:
    """Verifies **kern -> MusicXML conversion on clean and partially malformed SMT **kern output."""
    clean_kern = (
        '**kern\t**kern\n*clefF4\t*clefG2\n*k[f#]\t*k[f#]\n*M4/4\t*M4/4\n'
        '4G\t4g 4b\n4A\t4a\n2B\t2b\n=\t=\n2r\t2r\n2G\t2g\n*-\t*-'
    )
    out1 = TMP / 'kern_clean.musicxml'
    ok1, mode1 = kern_to_musicxml(clean_kern, out1, title='clean')
    assert ok1, f'clean kern conversion failed: {mode1}'
    p1 = read_musicxml(out1)
    assert sum(len(s) for s in p1['notes']) >= 8

    noisy_kern = '*clefF4\t*clefG2\n*M3/4\t*M3/4\n4·C\t4·c@ 4·e\n4·D\t4·d\n4·E\t4·e\n=\t=\n2.·C\t2.·c'
    out2 = TMP / 'kern_noisy.musicxml'
    ok2, mode2 = kern_to_musicxml(noisy_kern, out2, title='noisy')
    assert ok2, f'noisy kern conversion failed: {mode2}'
    p2 = read_musicxml(out2)
    assert sum(len(s) for s in p2['notes']) >= 6
    print(f'    clean={mode1} ({sum(len(s) for s in p1["notes"])} notes), noisy={mode2} ({sum(len(s) for s in p2["notes"])} notes)')


def test_systems_crop_and_smt_offline() -> None:
    """Tests ScoreReader systems.py cropping + live offline SMT++ full-page and system-cropped inference."""
    png = _ensure_smoke_satb_png()
    crops = crop_systems_with_scorereader(png, TMP / 'sys_crops', 'smoke_satb')
    assert len(crops) >= 1, 'systems.py produced zero crops on Verovio SATB page'

    fp_job = [{
        'id': 'smoke_satb',
        'images': [str(png)],
        'kern_out': str(TMP / 'smt_fp' / 'smoke_satb.krn'),
        'xml_out': str(TMP / 'smt_fp' / 'smoke_satb.musicxml'),
    }]
    fp_res = run_smt_batch('PRAIG/smt-fp-grandstaff', 'fp', fp_job, TMP / 'smt_fp', max_tokens=200, threads=6)
    assert fp_res['missing_keys'] == 0, f'smt_fp had missing keys: {fp_res["missing_keys"]}'
    assert fp_res['results'][0]['tokens'] > 10 and fp_res['results'][0]['xml_ok']

    sys_job = [{
        'id': 'smoke_satb',
        'images': [c['path'] for c in crops[:1]],
        'kern_out': str(TMP / 'smt_sys' / 'smoke_satb.krn'),
        'xml_out': str(TMP / 'smt_sys' / 'smoke_satb.musicxml'),
    }]
    sys_res = run_smt_batch('antoniorv6/smt-grandstaff', 'sys', sys_job, TMP / 'smt_sys', max_tokens=160, threads=6)
    assert sys_res['missing_keys'] == 0 and sys_res['is_legacy'] is True
    krn_txt = Path(sys_res['results'][0]['kern_out']).read_text(encoding='utf-8')
    assert '**ekern' in krn_txt or '*clef' in krn_txt, f'unexpected legacy SMT header: {krn_txt[:120]}'
    assert sys_res['results'][0]['xml_ok']
    print(
        f"    systems={len(crops)} | smt_fp: {fp_res['results'][0]['seconds']}s, {fp_res['results'][0]['tokens']} toks | "
        f"smt_sys: {sys_res['results'][0]['seconds']}s, {sys_res['results'][0]['tokens']} toks (legacy end_relu=True)"
    )


def test_oemer_and_scorereader_smoke() -> None:
    """Runs live offline ScoreReader and oemer ONNX on the same Verovio SATB smoke page."""
    png = _ensure_smoke_satb_png()
    sr_xml, sr_sec = run_scorereader_on_png(png, title='smoke_satb')
    assert sr_xml is not None, 'ScoreReader returned None on smoke SATB page'
    sr_path = TMP / 'smoke_sr.musicxml'
    sr_path.write_text(sr_xml, encoding='utf-8')
    sr_notes = sum(len(s) for s in read_musicxml(sr_path)['notes'])
    assert sr_notes >= 40, f'ScoreReader read unexpectedly few notes: {sr_notes}'

    oemer_out = TMP / 'oemer' / 'smoke_satb.musicxml'
    res = run_oemer_on_png(png, oemer_out, threads=12)
    assert res['ok'], f'oemer offline inference failed: {res}'
    oe_notes = sum(len(s) for s in read_musicxml(oemer_out)['notes'])
    assert oe_notes >= 10, f'oemer read unexpectedly few notes: {oe_notes}'
    print(f"    scorereader: {sr_sec:.2f}s ({sr_notes} notes) | oemer: {res['seconds']:.2f}s ({oe_notes} notes)")


TESTS = (
    test_verovio_offline,
    test_kern_converter_resilience,
    test_systems_crop_and_smt_offline,
    test_legato_offline,
    test_oemer_and_scorereader_smoke,
)


def main() -> int:
    TMP.mkdir(parents=True, exist_ok=True)
    passed = failed = 0
    t_all = time.time()
    for fn in TESTS:
        t0 = time.time()
        try:
            fn()
            print(f'  PASS {fn.__name__} ({time.time() - t0:.1f}s)', flush=True)
            passed += 1
        except Exception:
            print(f'  FAIL {fn.__name__} ({time.time() - t0:.1f}s)', flush=True)
            traceback.print_exc()
            failed += 1
    print(f'\nExternal OMR tests: {passed}/{len(TESTS)} passed, {failed} failed in {time.time() - t_all:.1f}s')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())

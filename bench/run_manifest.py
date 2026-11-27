#!/usr/bin/env python3
"""Runs scoreread in parallel over all scores in a JSON manifest (such as out/eval/clean_dev.json).

Uses `scoreread hymn` so multi-page key voting and clef carryover match real hymn reading.
Passes `--drawing off` by default when benchmarking scan recognition.

Usage:
  PY="$SCOREREAD_KIT/tools/copisteria/.venv/bin/python"
  $PY bench/run_manifest.py --manifest out/eval/clean_dev.json --out out/eval/run_baseline --jobs 12
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_case(case: dict, out_dir: Path, python_exe: str, drawing: str, extra: list[str]) -> tuple[str, int, float, str]:
    start = time.time()
    cid = case['id']
    pages_arg = ','.join(str(p) for p in case['pages'])
    cmd = [
        python_exe, '-m', 'scorereader', 'hymn', case['pdf'],
        '--pages', pages_arg,
        '--name', cid,
        '--out', str(out_dir),
        '--drawing', drawing,
        *extra,
    ]
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, env=env)
    elapsed = time.time() - start
    # Rename outputs from -p1..-pK to exact PDF page numbers if case['pages'] does not start at 1.
    if proc.returncode == 0 and case['pages'] != list(range(1, len(case['pages']) + 1)):
        # Collect written sequential files first to avoid clobbering during rename.
        staged = []
        for seq_idx, pdf_page in enumerate(case['pages'], 1):
            src = out_dir / f'{cid}-p{seq_idx}.musicxml'
            if src.exists():
                tmp = out_dir / f'.tmp_{cid}-p{pdf_page}.musicxml'
                src.rename(tmp)
                staged.append((tmp, out_dir / f'{cid}-p{pdf_page}.musicxml'))
        for tmp, dst in staged:
            tmp.rename(dst)
    log_dir = out_dir / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / f'{cid}.log').write_text(proc.stdout + '\n' + proc.stderr, encoding='utf-8')
    return cid, proc.returncode, elapsed, (proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else '')


def main() -> int:
    parser = argparse.ArgumentParser(description='Run scoreread over a manifest in parallel.')
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--python', default=sys.executable)
    parser.add_argument('--jobs', type=int, default=10)
    parser.add_argument('--drawing', choices=['auto', 'off'], default='off')
    parser.add_argument('--headnet', default=None, help='Pass --headnet VALUE to scorereader (e.g. off)')
    parser.add_argument('--extra', nargs='*', default=[])
    args = parser.parse_args()
    extra = list(args.extra)
    if args.headnet is not None:
        extra = ['--headnet', args.headnet] + extra

    manifest = json.loads(Path(args.manifest).read_text(encoding='utf-8'))
    cases = manifest['cases']
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    ok = fail = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futs = [pool.submit(run_case, c, out_dir, args.python, args.drawing, extra) for c in cases]
        for fut in concurrent.futures.as_completed(futs):
            cid, code, sec, err = fut.result()
            if code == 0:
                ok += 1
            else:
                fail += 1
                print(f'FAIL {cid} (code={code}, {sec:.1f}s): {err}', file=sys.stderr)
    print(f'Done: {ok}/{len(cases)} ok, {fail} failed in {time.time() - t0:.1f}s -> {out_dir}')
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main())

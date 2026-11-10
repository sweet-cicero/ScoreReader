#!/usr/bin/env python3
"""Runs copisteria on one image with the experiment's options, and writes what it saw for each note.

usage: cop.py image.png out_folder [--imgsz N] [--per-system N] [--ledger MODES] [--name NAME]

Run it with copisteria's own Python, from any folder. Output: <out>/<name>.musicxml and <out>/<name>.notes.json
(for each note head: its box, staff, bar, staff position, class, voice and the model's confidence).

--imgsz N        run the symbol detector with the image's long side at N px (a multiple of 32). copisteria picks the
                 size that puts the staff space at 10.6 px; a larger size shows the detector more detail.
--per-system N   the staves of each system, when it is known (1 for a melody line, 2 for SA over TB). copisteria
                 decides the systems from the ink at the left of the staves, and a shadow of the binding there makes
                 it join staves that do not belong together. With this option, each N staves from the top make a
                 system. When the number of staves on the page is not a multiple of N, or copisteria found one staff
                 twice, copisteria decides as usual.
--ledger MODES   the ledger rule (see ledger.py): both, out or in. With several modes (commas between them), the
                 first goes to <out> and each other mode to <out>-<mode>; the mode "none" writes the plain reading.
"""
import argparse
import copy
import json
import shutil
import sys
import tempfile
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT / 'tools' / 'copisteria' / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from PIL import Image  # noqa: E402
from copisteria import front, read, write  # noqa: E402
from copisteria.detect import Detector  # noqa: E402
from copisteria.paths import EVIDENCE, detector  # noqa: E402
from copisteria.pipeline import inputs  # noqa: E402
from copisteria.revise import read_revised  # noqa: E402


def notes_of(rd):
    out = []
    for sym in rd.layout.syms:
        token = rd.tok.get(sym.i)
        if not token or not str(token['cls']['v']).startswith('note'):
            continue
        staff = rd.layout.staves[sym.staff] if sym.staff >= 0 else None
        out.append({'i': sym.i, 'box': [round(float(v), 1) for v in sym.box], 'staff': sym.staff, 'bar': sym.bar,
                    'cls': token['cls']['v'], 'cls_p': token['cls']['p'], 'real': token['real']['p'],
                    'pos': token['pos']['v'], 'pos_p': token['pos']['p'], 'voice': token['voice']['v'],
                    'chord': token.get('chord'), 'onset': token.get('onset'),
                    'staff_y0': None if staff is None else round(float(staff.y0), 1),
                    'staff_y1': None if staff is None else round(float(staff.y1), 1),
                    'sp': None if staff is None else round(float(staff.sp), 2)})
    return out


def force_systems(per_system):
    """Makes copisteria put each per_system staves, from the top, into one system."""
    original = front._systems

    def forced(syms, staves, gray=None, ink=False, levels=None):
        # copisteria sometimes finds one hand-drawn staff twice, a few px apart. Then a count from the top is wrong.
        twice = any(staves[k + 1].y0 - staves[k].y0 < 2 * staves[k].sp for k in range(len(staves) - 1))
        if len(staves) % per_system or twice:
            return original(syms, staves, gray, ink, levels)
        index = {id(staff): k for k, staff in enumerate(staves)}
        saved = front._ink_links, front._opening_line, front._pale_line

        def ink_links(gray_, syms_, a, b, page_left):
            return (1.0, 1.0) if index[id(b)] % per_system else (0.0, 0.0)

        front._ink_links = ink_links
        front._opening_line = lambda *a, **k: 0.0
        front._pale_line = lambda *a, **k: 0.0
        try:
            return original(syms, staves, gray, ink, levels)
        finally:
            front._ink_links, front._opening_line, front._pale_line = saved

    front._systems = forced


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('image')
    parser.add_argument('out')
    parser.add_argument('--imgsz', type=int, default=0)
    parser.add_argument('--ledger', default='')
    parser.add_argument('--name', default=None)
    parser.add_argument('--per-system', type=int, default=0)
    args = parser.parse_args()
    if args.per_system:
        force_systems(args.per_system)
    name = args.name or Path(args.image).stem
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='cop-', dir=out))
    try:
        png = work / (name + '.png')
        shutil.copy(args.image, png)
        image = Image.open(png).convert('L')
        if args.imgsz:
            det = Detector()
            array, scale = det.prepare(image, args.imgsz)
            dets = det.run_array(array, scale)
            png.with_name(f'{png.stem}.dets_{detector()[1]}_{args.imgsz}.json').write_text(json.dumps(dets))
        model = read.load_model(str(EVIDENCE), 'cpu')
        dets, cands, feats = inputs(png, model)
        rd = read_revised(dets, image.width, image.height, model, device='cpu', image=image, cands=cands, feats=feats)
        sizes = [path.stem.rsplit('_', 1)[1] for path in work.glob('*.dets_*.json')]
        modes = [mode for mode in args.ledger.split(',') if mode] or ['none']
        clean = copy.deepcopy(rd.tok)
        for number, mode in enumerate(modes):
            rd.tok = copy.deepcopy(clean)
            changed = []
            if mode != 'none':
                import ledger
                changed = ledger.apply(rd, image, mode)
            folder = out if number == 0 else Path(f'{out}-{mode}')
            folder.mkdir(parents=True, exist_ok=True)
            (folder / f'{name}.musicxml').write_text(write.write(rd, texts=None, image=image))
            (folder / f'{name}.notes.json').write_text(json.dumps(
                {'notes': notes_of(rd), 'staves': len(rd.layout.staves), 'systems': len(rd.layout.systems),
                 'ledger_changes': changed, 'imgsz': sizes}))
            print(json.dumps({'name': name, 'mode': mode, 'notes': len(notes_of(rd)), 'staves': len(rd.layout.staves),
                              'systems': len(rd.layout.systems), 'ledger_changes': len(changed)}))
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == '__main__':
    main()

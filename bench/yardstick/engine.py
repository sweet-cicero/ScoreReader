"""The yardstick: reads the symbols of a clean page with copisteria (Apache-2.0), a local reader with a neural network.

This is no part of the engine. scoreread reads a page with rules alone and never loads this folder. The yardstick
shows on the same clean page, with the same staves and systems, what a network reads, so each own rule can be
measured against it. Version 0.4 of the reader used this step; version 0.5 replaced it.

copisteria gets the staves and the systems of scoreread as facts (it finds a bent or tilted staff twice or not at
all), and the notes on the first ledger line can be checked with a rule (ledger.py), as an option.

Where copisteria is installed: the folder in SCOREREAD_COPISTERIA, or tools/copisteria in the test kit (the folder in
SCOREREAD_KIT; see the README).
"""
from __future__ import annotations

import copy
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT = Path(os.environ.get('SCOREREAD_KIT', Path.home() / 'Projects' / 'LitChoir' / 'tmp' / 'omr-test'))
COPISTERIA = Path(os.environ.get('SCOREREAD_COPISTERIA', KIT / 'tools' / 'copisteria'))


def _load():
    source = str(COPISTERIA / 'src')
    if not (COPISTERIA / 'src' / 'copisteria').is_dir():
        raise SystemExit(f'scoreread: copisteria is not in {COPISTERIA}. Set SCOREREAD_COPISTERIA to its folder, or '
                         'SCOREREAD_KIT to the test kit that holds tools/copisteria.')
    if source not in sys.path:
        sys.path.insert(0, source)
    from copisteria import front, read, write  # noqa: PLC0415
    from copisteria.paths import EVIDENCE  # noqa: PLC0415
    from copisteria.pipeline import inputs  # noqa: PLC0415
    from copisteria.revise import read_revised  # noqa: PLC0415
    return front, read, write, EVIDENCE, inputs, read_revised


def _force_systems(front, places: list[dict]):
    """Makes copisteria put its staves into the systems of the clean page. Returns a function that undoes it."""
    original = front._systems

    def system_of(staff) -> int:
        middle = (staff.y0 + staff.y1) / 2
        for number, place in enumerate(places):
            if place['top'] <= middle < place['bottom']:
                return number
        return min(range(len(places)), key=lambda number: abs((places[number]['top'] + places[number]['bottom']) / 2 - middle))

    def forced(syms, staves, gray=None, ink=False, levels=None):
        owner = {id(staff): system_of(staff) for staff in staves}
        before = {id(staff): owner[id(staves[index - 1])] if index else None for index, staff in enumerate(staves)}
        saved = front._ink_links, front._opening_line, front._pale_line

        def ink_links(gray_, syms_, a, b, page_left):
            return (1.0, 1.0) if owner[id(b)] == before[id(b)] else (0.0, 0.0)

        front._ink_links = ink_links
        front._opening_line = lambda *a, **k: 0.0
        front._pale_line = lambda *a, **k: 0.0
        try:
            return original(syms, staves, gray, ink, levels)
        finally:
            front._ink_links, front._opening_line, front._pale_line = saved

    front._systems = forced

    def undo():
        front._systems = original

    return undo


def _force_staves(front, places: list[dict], height: int):
    """Makes copisteria use the staves of the clean page. Returns a function that undoes it. copisteria still adds a
    staff of its own where a row of its bar boxes stands far from every staff: a staff whose lines the copy lost."""
    import numpy as np  # noqa: PLC0415
    from copisteria.vision.page import staves as module  # noqa: PLC0415
    original = module.find_staves
    found = []
    for place in places:
        for rows, (x0, x1) in zip(place['lines'], place['x']):
            found.append(module.Staff(lines=[module.Line(y=float(row), x0=int(x0), x1=int(x1), thickness=3, score=1.0)
                                             for row in rows]))
    found.sort(key=lambda staff: staff.top)
    every = [line for staff in found for line in staff.lines]

    def forced(image, *args, **kwargs):
        return module.StaffMap(staves=list(found), lines=list(every), profile=np.zeros(height), ink_threshold=128,
                               cover_threshold=0.5)

    module.find_staves = forced

    def undo():
        module.find_staves = original

    return undo


def notes_of(rd) -> list[dict]:
    """Each note head of a reading: its box on the clean page, staff, bar, staff position, class, voice and how sure
    copisteria is of each."""
    out = []
    for sym in rd.layout.syms:
        token = rd.tok.get(sym.i)
        if not token or not str(token['cls']['v']).startswith('note'):
            continue
        staff = rd.layout.staves[sym.staff] if sym.staff >= 0 else None
        out.append({'i': sym.i, 'box': [round(float(v), 1) for v in sym.box], 'staff': sym.staff, 'bar': sym.bar,
                    'cls': token['cls']['v'], 'cls_p': token['cls']['p'], 'real': token['real']['p'],
                    'pos': token['pos']['v'], 'pos_p': token['pos']['p'], 'voice': token['voice']['v'],
                    'staff_y0': None if staff is None else round(float(staff.y0), 1),
                    'staff_y1': None if staff is None else round(float(staff.y1), 1),
                    'sp': None if staff is None else round(float(staff.sp), 2)})
    return out


def read_page(image_path: str | Path, places: list[dict], ledger: bool = False) -> dict:
    """Reads a clean page. Returns {'musicxml': text, 'notes': [...], 'staves': n, 'systems': n, 'ledger': [...]}."""
    from PIL import Image  # noqa: PLC0415
    front, read, write, evidence, inputs, read_revised = _load()
    work = Path(tempfile.mkdtemp(prefix='scoreread-'))
    png = work / 'page.png'
    shutil.copy(image_path, png)
    image = Image.open(png).convert('L')
    undo_systems = _force_systems(front, places) if places else (lambda: None)
    undo_staves = _force_staves(front, places, image.height) if places else (lambda: None)

    def undo():
        undo_systems()
        undo_staves()

    try:
        model = read.load_model(str(evidence), 'cpu')
        dets, cands, feats = inputs(png, model)
        rd = read_revised(dets, image.width, image.height, model, device='cpu', image=image, cands=cands, feats=feats)
        import choir  # noqa: PLC0415
        tenors = choir.tenor_clef(rd)
        changed = []
        if ledger:
            import ledger as rule  # noqa: PLC0415
            changed = rule.apply(rd, image)
        return {'musicxml': write.write(rd, texts=None, image=image), 'notes': notes_of(rd),
                'staves': len(rd.layout.staves), 'systems': len(rd.layout.systems), 'ledger': changed,
                'tenor_staves': tenors}
    finally:
        undo()
        shutil.rmtree(work, ignore_errors=True)

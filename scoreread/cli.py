"""The command: a page of a score in, its notes out. Everything runs on this computer.

usage: python -m scoreread read <page.png | score.pdf> --out <folder> [--page N] [--name NAME]
                                [--symbols own | copisteria] [--ledger]
       python -m scoreread layers <page.png | score.pdf> --out <folder> [--page N]
       python -m scoreread layout <page.png | score.pdf> --out <folder> [--page N]

read    finds the staves and the systems, builds the clean page, reads it, and writes:
          <name>.musicxml     the notes
          <name>.notes.json   each note with its place on the clean page and what it was read from
          <name>.layout.json  the staves and systems that were found
          <name>.clean.png    the clean page that was read
          <name>.staves.png   the scan with the staves drawn on it (small), as a check
          <name>.layers.png   the clean page with each layer of ink in its own colour (own symbol step only)
layers  does the first steps and writes the picture of the layers (no reading), to check a hard page at a glance.
layout  does only the first steps (no reading), to check a page fast.

--symbols names the symbol step. `own` (the default) reads the symbols with rules on the ink: no model, and only
OpenCV and NumPy are needed. `copisteria` reads them with copisteria's network, as a yardstick; it needs copisteria
(see the README), and --ledger turns the ledger rule on for it (see ledger.py).

A PDF page is made into an image at 300 dpi with pdftoppm.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import cv2

from .page import clean_page
from .staves import draw, find_staves
from .systems import find_systems, lost_staves


def load(path: Path, page: int) -> tuple:
    """The page as a grey image, and a name for its output files."""
    if path.suffix.lower() == '.pdf':
        with tempfile.TemporaryDirectory() as folder:
            stem = Path(folder) / 'page'
            subprocess.run(['pdftoppm', '-r', '300', '-gray', '-f', str(page), '-l', str(page), '-singlefile', '-png',
                            str(path), str(stem)], check=True)
            grey = cv2.imread(str(stem) + '.png', cv2.IMREAD_GRAYSCALE)
        return grey, f'{path.stem}-p{page}'
    return cv2.imread(str(path), cv2.IMREAD_GRAYSCALE), path.stem


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog='scoreread', description='Reads a page of a score on this computer.')
    parser.add_argument('command', choices=['read', 'layers', 'layout'])
    parser.add_argument('source')
    parser.add_argument('--out', required=True)
    parser.add_argument('--page', type=int, default=1)
    parser.add_argument('--symbols', choices=['own', 'copisteria'], default='own')
    parser.add_argument('--ledger', action='store_true')
    parser.add_argument('--name', default=None)
    args = parser.parse_args(argv)
    start = time.time()
    grey, name = load(Path(args.source), args.page)
    if grey is None:
        print(f'scoreread: cannot open {args.source}. Give a PNG image or a PDF file.', file=sys.stderr)
        return 2
    name = args.name or name
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    staves = find_staves(grey)
    if not staves:
        print(f'scoreread: no staff found on {args.source}. Check that the page is upright and holds music.', file=sys.stderr)
        return 1
    systems = find_systems(grey, staves)
    staves, systems = lost_staves(grey, staves, systems)
    page, places = clean_page(grey, staves, systems)
    cv2.imwrite(str(out / f'{name}.clean.png'), page)
    cv2.imwrite(str(out / f'{name}.staves.png'), cv2.resize(draw(grey, staves), None, fx=0.4, fy=0.4, interpolation=cv2.INTER_AREA))
    layout = {'source': str(args.source), 'page': args.page, 'width': int(grey.shape[1]), 'height': int(grey.shape[0]),
              'staves': staves, 'systems': systems, 'clean_page': places}
    (out / f'{name}.layout.json').write_text(json.dumps(layout))
    summary = {'name': name, 'staves': len(staves), 'systems': [len(system) for system in systems]}
    if args.command == 'layers' or (args.command == 'read' and args.symbols == 'own'):
        from .layers import picture, read_layers  # noqa: PLC0415
        from .reader import read_page  # noqa: PLC0415
        if args.command == 'layers':
            cv2.imwrite(str(out / f'{name}.layers.png'), picture(read_layers(page, places)))
        else:
            result = read_page(page, places, title=name)
            cv2.imwrite(str(out / f'{name}.layers.png'), picture(result['layers']))
            (out / f'{name}.musicxml').write_text(result['musicxml'])
            (out / f'{name}.notes.json').write_text(json.dumps(
                {'notes': result['notes'], 'staves': result['staves'], 'systems': result['systems'],
                 'key': result['key'], 'clefs': result['clefs'], 'space': result['layers']['space']}))
            summary.update(symbols='own', notes=len(result['notes']), key=result['key'], clefs=result['clefs'])
    elif args.command == 'read':
        from .engine import read_page  # noqa: PLC0415
        result = read_page(out / f'{name}.clean.png', places, ledger=args.ledger)
        (out / f'{name}.musicxml').write_text(result['musicxml'])
        (out / f'{name}.notes.json').write_text(json.dumps(
            {'notes': result['notes'], 'staves': result['staves'], 'systems': result['systems'], 'ledger': result['ledger']}))
        summary.update(symbols='copisteria', notes=len(result['notes']), reader_staves=result['staves'],
                       reader_systems=result['systems'], ledger_changes=len(result['ledger']),
                       tenor_staves=len(result['tenor_staves']))
    summary['seconds'] = round(time.time() - start, 1)
    print(json.dumps(summary))
    return 0


if __name__ == '__main__':
    sys.exit(main())

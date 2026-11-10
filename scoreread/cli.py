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

A PDF that notation software wrote (Finale, MuseScore, Encore) is read from its own drawing, with its words: every
sign is a character of a music font at its exact place (scoreread.vector; needs pdfplumber). --drawing off reads such
a page as an image instead.

--symbols names the symbol step. `own` (the default) reads the symbols with rules on the ink: no model, and only
OpenCV and NumPy are needed. `copisteria` reads them with copisteria's network, as a yardstick; it needs copisteria
(see the README), and --ledger turns the ledger rule on for it (see ledger.py).

A PDF page is made into an image at 300 dpi with pdftoppm. A page that is a photo kept with no size of its own (a
phone picture at 72 dpi makes a page of 42 by 56 inches) is made as long as an A4 page at 300 dpi.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import cv2

from .page import clean_page, flat_paper
from .staves import draw, find_staves
from .systems import find_systems, lost_staves


PAGE_MAX = 17.0     # inches: a longer PDF page is a picture that was kept with no size of its own
PAGE_LONG = 3508    # pixels: such a page is made this long, as an A4 page at 300 dpi


def render(path, page: int, stem) -> None:
    """Makes <stem>.png of a PDF page: at 300 dpi, or as long as an A4 page when the page has no true size."""
    told = subprocess.run(['pdfinfo', '-f', str(page), '-l', str(page), str(path)], capture_output=True, text=True).stdout
    size = re.search(r'Page\s+%d size:\s+([\d.]+) x ([\d.]+) pts' % page, told)
    huge = size is not None and max(float(size.group(1)), float(size.group(2))) / 72 > PAGE_MAX
    scale = ['-scale-to', str(PAGE_LONG)] if huge else ['-r', '300']
    subprocess.run(['pdftoppm', *scale, '-gray', '-f', str(page), '-l', str(page), '-singlefile', '-png', str(path),
                    str(stem)], check=True)


def load(path: Path, page: int) -> tuple:
    """The page as a grey image, and a name for its output files."""
    if path.suffix.lower() == '.pdf':
        with tempfile.TemporaryDirectory() as folder:
            stem = Path(folder) / 'page'
            render(path, page, stem)
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
    parser.add_argument('--drawing', choices=['auto', 'off'], default='auto')
    parser.add_argument('--key-before', type=int, default=None,
                        help='the key of the page before in the same hymn (sharps +, flats -), for a page that shows no key signature')
    args = parser.parse_args(argv)
    start = time.time()
    if args.command == 'read' and args.symbols == 'own' and args.drawing == 'auto' and Path(args.source).suffix.lower() == '.pdf':
        # A PDF that notation software wrote holds its signs and its words as they are: no image is read.
        try:
            from .vector import read_pdf_page  # noqa: PLC0415
            result = read_pdf_page(Path(args.source), args.page, title=args.name or '')
        except ImportError:
            result = None       # pdfplumber is not installed: the page is read as an image
        if result is not None:
            name = args.name or f'{Path(args.source).stem}-p{args.page}'
            out = Path(args.out)
            out.mkdir(parents=True, exist_ok=True)
            (out / f'{name}.musicxml').write_text(result['musicxml'])
            (out / f'{name}.notes.json').write_text(json.dumps(
                {'notes': result['notes'], 'staves': result['staves'], 'systems': result['systems'], 'key': result['key'],
                 'clefs': result['clefs'], 'drawing': True}))
            print(json.dumps({'name': name, 'staves': result['staves'], 'systems': result['systems'], 'symbols': 'drawing',
                              'notes': len(result['notes']), 'syllables': sum(1 for note in result['notes'] if note.get('lyric')),
                              'key': result['key'], 'clefs': result['clefs'], 'seconds': round(time.time() - start, 1)}))
            return 0
    grey, name = load(Path(args.source), args.page)
    if grey is None:
        print(f'scoreread: cannot open {args.source}. Give a PNG image or a PDF file.', file=sys.stderr)
        return 2
    grey = flat_paper(grey)
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
            result = read_page(page, places, title=name, key_before=args.key_before)
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

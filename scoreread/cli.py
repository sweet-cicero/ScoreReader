"""The command: a page of a score in, its notes out. Everything runs on this computer.

usage: python -m scoreread read <page.png | score.pdf> --out <folder> [--page N] [--name NAME] [--key-before K] [--words FILE]
       python -m scoreread hymn <score.pdf | page1.png page2.png ...> --out <folder> [--pages 2-4] [--name NAME] [--words FILE]
       python -m scoreread layers <page.png | score.pdf> --out <folder> [--page N]
       python -m scoreread layout <page.png | score.pdf> --out <folder> [--page N]

read    finds the staves and the systems, builds the clean page, reads it, and writes:
          <name>.musicxml     the notes
          <name>.notes.json   each note with its place on the clean page and what it was read from
          <name>.layout.json  the staves and systems that were found
          <name>.clean.png    the clean page that was read
          <name>.staves.png   the scan with the staves drawn on it (small), as a check
          <name>.layers.png   the clean page with each layer of ink in its own colour
hymn    reads the pages of a hymn in order (all pages of a PDF, or those of --pages; or some images) and joins
        them: <name>.musicxml holds the whole hymn, each staff of the systems as one part, and <name>.hymn.json says
        what was read on each page. Each page is also written as `read` writes it (<name>-p1..., counted from the
        first page that was read). The staves of all pages vote together for the key of the hymn; a page keeps
        another key only where most of its staves show it clearly. A page that shows no key signature has the key
        of the page before, and the staves keep their clefs from page to page unless a page shows others.
layers  does the first steps and writes the picture of the layers (no reading), to check a hard page at a glance.
layout  does only the first steps (no reading), to check a page fast.

A PDF that notation software wrote (Finale, MuseScore, Encore) is read from its own drawing, with its words: every
sign is a character of a music font at its exact place (scoreread.vector; needs pdfplumber). --drawing off reads such
a page as an image instead.

The symbols are read with rules on the ink: no model, and only OpenCV and NumPy are needed. --key-before gives the
key of the page before in the same hymn (sharps +, flats -), for a page that shows no key signature.

--words gives a list of words (a text file: plain text, or lines of a word and its count; SCOREREAD_WORDS names it
too). With it the words of a scan are read: the letter shapes of the hymn are grouped, and the groups are named so
that the page reads like the words of the list (scoreread.letters, scoreread.lyrics). `hymn` reads the words of all
pages together, which names the letters better than one page alone. Without a list a scan gives its notes only.

A PDF page is made into an image at 300 dpi with pdftoppm. A page that is a photo kept with no size of its own (a
phone picture at 72 dpi makes a page of 42 by 56 inches) is made as long as an A4 page at 300 dpi.
"""
from __future__ import annotations

import argparse
import json
import os
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


def prepare(source: Path, page: int) -> dict | None:
    """The first steps on the image of a page: {'grey', 'stem' (a name for its files), 'staves', 'systems', 'clean',
    'places'}; None when the file cannot be opened. A page with no staff has no 'clean'."""
    grey, stem = load(source, page)
    if grey is None:
        return None
    grey = flat_paper(grey)
    staves = find_staves(grey)
    ready = {'grey': grey, 'stem': stem, 'staves': staves}
    if staves:
        systems = find_systems(grey, staves)
        ready['staves'], ready['systems'] = lost_staves(grey, staves, systems)
        ready['clean'], ready['places'] = clean_page(grey, ready['staves'], ready['systems'])
    return ready


def drawn(source: Path, page: int, name: str | None) -> dict | None:
    """What the drawing of a PDF page gives, when notation software wrote it: no image is read. None for a scan,
    and when pdfplumber is not installed (the page is then read as an image)."""
    if source.suffix.lower() != '.pdf':
        return None
    try:
        from .vector import read_pdf_page  # noqa: PLC0415
        return read_pdf_page(source, page, title=name or '')
    except ImportError:
        return None


def word_list(path: str | None):
    """The list of words for the words of a scan: from the file of --words, or of SCOREREAD_WORDS. None without one."""
    path = path or os.environ.get('SCOREREAD_WORDS')
    if not path:
        return None
    from .lyrics import load_words  # noqa: PLC0415
    return load_words(path)


def set_words(read: list[dict], lex, shapes: str | None = None, name: str = '') -> int:
    """Reads the words of the pages of a hymn that were read as images, all pages together (one copyist draws a
    letter the same way on each page), and sets each syllable under its note. Returns how many were set.

    `shapes` names a file of letter shapes (--shapes): the shapes that earlier hymns named help to name the letters
    of this hymn, and the shapes that this hymn names are added to the file under `name` (in place of the ones it
    held under that name)."""
    from .letters import page_glyphs  # noqa: PLC0415
    from .lyrics import load_shapes, read_words, save_shapes, set_under  # noqa: PLC0415
    from .music import musicxml  # noqa: PLC0415
    images = [(number, result) for number, result in enumerate(read) if result.get('layers')]
    glyphs = [glyph for number, result in images for glyph in page_glyphs(result['layers'], number)]
    if shapes:
        known = [shape for shape in load_shapes(shapes) if shape['source'] != name]
        learned: list[dict] = []
        syllables = read_words(glyphs, lex, known, learned, name)
        if learned:
            save_shapes(shapes, known + learned)
    else:
        syllables = read_words(glyphs, lex)
    count = 0
    for number, result in images:
        count += set_under(result, syllables, number)
        result['musicxml'] = musicxml(result['parts'], result.get('title', ''))
    return count


def write_page(out: Path, name: str, result: dict) -> None:
    """Writes what was read on a page that was read as an image: its notes as MusicXML and as a list."""
    (out / f'{name}.musicxml').write_text(result['musicxml'])
    (out / f'{name}.notes.json').write_text(json.dumps(
        {'notes': result['notes'], 'staves': result['staves'], 'systems': result['systems'],
         'key': result['key'], 'clefs': result['clefs'], 'space': result['layers']['space']}))


def read_one(command: str, source: Path, page: int, out: Path, name: str | None = None, drawing: str = 'auto',
             key_before: int | None = None, clefs_before: list[str] | None = None, key_hymn: int | None = None,
             looked: tuple | None = None, lex=None, shapes: str | None = None) -> tuple[int, dict, dict | None]:
    """Does `command` ('read', 'layers' or 'layout') on one page and writes its files to `out`. Returns the exit
    code, the summary that the command prints, and what the reader gave (None when nothing was read). `looked` is
    what a first look at the page gave already: (the drawing's result or None, what prepare() gave or None). With
    `lex` (a list of words) the words of an image page are read too."""
    start = time.time()
    out.mkdir(parents=True, exist_ok=True)
    result, ready = looked if looked else (None, None)
    if command == 'read' and drawing == 'auto' and result is None and looked is None:
        # A PDF that notation software wrote holds its signs and its words as they are: no image is read.
        result = drawn(source, page, name)
    if result is not None:
        name = name or f'{source.stem}-p{page}'
        (out / f'{name}.musicxml').write_text(result['musicxml'])
        (out / f'{name}.notes.json').write_text(json.dumps(
            {'notes': result['notes'], 'staves': result['staves'], 'systems': result['systems'], 'key': result['key'],
             'clefs': result['clefs'], 'drawing': True}))
        return 0, {'name': name, 'staves': result['staves'], 'systems': result['systems'], 'symbols': 'drawing',
                   'notes': len(result['notes']), 'syllables': sum(1 for note in result['notes'] if note.get('lyric')),
                   'key': result['key'], 'clefs': result['clefs'], 'seconds': round(time.time() - start, 1)}, result
    ready = ready or prepare(source, page)
    if ready is None:
        print(f'scoreread: cannot open {source}. Give a PNG image or a PDF file.', file=sys.stderr)
        return 2, {}, None
    grey, staves = ready['grey'], ready['staves']
    name = name or ready['stem']
    if not staves:
        print(f'scoreread: no staff found on {source}' + (f', page {page}' if source.suffix.lower() == '.pdf' else '')
              + '. Check that the page is upright and holds music.', file=sys.stderr)
        return 1, {'name': name, 'staves': 0}, None
    systems, clean, places = ready['systems'], ready['clean'], ready['places']
    cv2.imwrite(str(out / f'{name}.clean.png'), clean)
    cv2.imwrite(str(out / f'{name}.staves.png'), cv2.resize(draw(grey, staves), None, fx=0.4, fy=0.4, interpolation=cv2.INTER_AREA))
    layout = {'source': str(source), 'page': page, 'width': int(grey.shape[1]), 'height': int(grey.shape[0]),
              'staves': staves, 'systems': systems, 'clean_page': places}
    (out / f'{name}.layout.json').write_text(json.dumps(layout))
    summary = {'name': name, 'staves': len(staves), 'systems': [len(system) for system in systems]}
    result = None
    if command in ('layers', 'read'):
        from .layers import picture, read_layers  # noqa: PLC0415
        from .reader import read_page  # noqa: PLC0415
        if command == 'layers':
            cv2.imwrite(str(out / f'{name}.layers.png'), picture(read_layers(clean, places)))
        else:
            result = read_page(clean, places, title=name, key_before=key_before, clefs_before=clefs_before, key_hymn=key_hymn)
            cv2.imwrite(str(out / f'{name}.layers.png'), picture(result['layers']))
            if lex:
                summary['syllables'] = set_words([result], lex, shapes, name)
            write_page(out, name, result)
            summary.update(symbols='own', notes=len(result['notes']), key=result['key'], clefs=result['clefs'])
    summary['seconds'] = round(time.time() - start, 1)
    return 0, summary, result


def page_numbers(source: Path, wanted: str | None) -> list[int]:
    """The pages of a source to read: those of `wanted` ('2-4' or '1,3,5'), or all pages of a PDF. An image is one page."""
    if source.suffix.lower() != '.pdf':
        return [1]
    if wanted:
        pages = []
        for piece in wanted.split(','):
            first, _, last = piece.partition('-')
            pages.extend(range(int(first), int(last or first) + 1))
        return pages
    told = subprocess.run(['pdfinfo', str(source)], capture_output=True, text=True).stdout
    count = re.search(r'Pages:\s+(\d+)', told)
    return list(range(1, int(count.group(1)) + 1)) if count else [1]


def read_hymn(sources: list[Path], out: Path, name: str | None = None, pages: str | None = None, drawing: str = 'auto',
              key_before: int | None = None, lex=None, shapes: str | None = None) -> tuple[int, dict]:
    """Reads the pages of a hymn in order and joins them: <name>.musicxml holds the whole hymn. Each page is also
    written as `read` writes it. The key signature holds for the whole hymn: a first look at every page lets the
    staves of all pages vote for it together. A page without a key signature has the key of the page before, and
    the clefs of the page before are a witness for the clefs of a page. With `lex` (a list of words) the words of
    the pages that were read as images are read too, all pages together."""
    from .hymn import join_pages  # noqa: PLC0415
    from .music import musicxml  # noqa: PLC0415
    from .reader import page_starts  # noqa: PLC0415
    from .starts import hymn_key  # noqa: PLC0415
    start = time.time()
    name = name or sources[0].stem
    # The first look: the first steps on each page, and what the start of each staff shows.
    looked, shown = [], []
    for source in sources:
        for page in page_numbers(source, pages):
            stem = f'{name}-p{len(looked) + 1}'
            result = drawn(source, page, stem) if drawing == 'auto' else None
            ready = prepare(source, page) if result is None else None
            if result is None and ready is None:
                print(f'scoreread: cannot open {source}. Give a PNG image or a PDF file.', file=sys.stderr)
                return 2, {}
            if ready is not None and ready['staves']:
                shown.append(page_starts(ready['clean'], ready['places']))
            looked.append((source, page, stem, (result, ready)))
    whole = hymn_key(shown)
    read, told, stems = [], [], []
    clefs_before = None
    for source, page, stem, first in looked:
        code, summary, result = read_one('read', source, page, out, stem, drawing, key_before, clefs_before, whole, first)
        told.append(dict(summary, source=str(source), page=page, read=result is not None))
        if result is not None:
            read.append(result)
            stems.append(stem)
            key_before = result['key']
            clefs_before = result.get('system_clefs') or clefs_before
    if not read:
        return 1, {'name': name, 'pages': told}
    if lex and set_words(read, lex, shapes, name):
        for stem, result in zip(stems, read):
            if result.get('layers'):
                write_page(out, stem, result)
    parts, names = join_pages(read)
    (out / f'{name}.musicxml').write_text(musicxml(parts, name, names))
    summary = {'name': name, 'pages': told, 'parts': len(parts), 'bars': max(len(part) for part in parts),
               'notes': sum(len(result['notes']) for result in read),
               'syllables': sum(1 for result in read for note in result['notes'] if note.get('lyric')),
               'seconds': round(time.time() - start, 1)}
    if whole is not None:
        summary['key'] = whole
    (out / f'{name}.hymn.json').write_text(json.dumps(summary))
    return 0, summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog='scoreread', description='Reads the pages of a score on this computer.')
    parser.add_argument('command', choices=['read', 'hymn', 'layers', 'layout'])
    parser.add_argument('source', nargs='+')
    parser.add_argument('--out', required=True)
    parser.add_argument('--page', type=int, default=1)
    parser.add_argument('--pages', default=None, help="for hymn: the pages of the PDF, as '2-4' or '1,3,5' (all pages without it)")
    parser.add_argument('--name', default=None)
    parser.add_argument('--drawing', choices=['auto', 'off'], default='auto')
    parser.add_argument('--words', default=None,
                        help='a text file with a list of words (or SCOREREAD_WORDS): the words of a scan are read with it')
    parser.add_argument('--shapes', default=None,
                        help='a file of letter shapes that the reader keeps (or SCOREREAD_SHAPES): what one hymn named helps the next')
    parser.add_argument('--key-before', type=int, default=None,
                        help='the key of the page before in the same hymn (sharps +, flats -), for a page that shows no key signature')
    args = parser.parse_args(argv)
    shapes = args.shapes or os.environ.get('SCOREREAD_SHAPES')
    if args.command == 'hymn':
        code, summary = read_hymn([Path(source) for source in args.source], Path(args.out), args.name, args.pages,
                                  args.drawing, args.key_before, word_list(args.words), shapes)
    else:
        if len(args.source) > 1:
            parser.error(f'{args.command} takes one page; `hymn` reads several')
        code, summary, _ = read_one(args.command, Path(args.source[0]), args.page, Path(args.out), args.name, args.drawing,
                                    args.key_before, lex=word_list(args.words) if args.command == 'read' else None, shapes=shapes)
    if summary:
        print(json.dumps(summary))
    return code


if __name__ == '__main__':
    sys.exit(main())
